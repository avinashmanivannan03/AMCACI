import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline as hf_pipeline
import hdbscan

from src.models.schemas import TranscriptSegment, ClusterResult
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_classifier = None


def _load_classifier():
    global _classifier
    if _classifier is None:
        logger.info("Loading zero-shot classifier: %s", settings.ZEROSHOT_MODEL)
        _classifier = hf_pipeline(
            "zero-shot-classification",
            model=settings.ZEROSHOT_MODEL,
            device=-1,
        )
    return _classifier


def _classify_text(text: str) -> tuple[str, float]:
    """
    Run zero-shot classification on a text string.
    Returns (top_label, confidence_score).
    """
    classifier = _load_classifier()
    result = classifier(
        text,
        candidate_labels=settings.NEWS_CATEGORIES,
        multi_label=False,
    )
    return result["labels"][0], float(result["scores"][0])


def _sliding_window_classify(
    segments: list[TranscriptSegment],
) -> list[str]:
    """
    Classify sentences using a sliding window of WINDOW_SIZE sentences with WINDOW_OVERLAP.

    For each window:
      1. Concatenate the window sentences and classify as a group.
      2. Assign the window's top category to all sentences in that window (provisional).

    Consecutive windows with the same category get the same label.
    Boundary detection happens in the reassignment step that follows.

    Returns a list of provisional category labels, one per segment.
    """
    n = len(segments)
    window_size = settings.WINDOW_SIZE
    overlap = settings.WINDOW_OVERLAP
    step = max(1, window_size - overlap)

    # provisional_labels[i] stores list of labels assigned to sentence i across all windows
    # We take majority vote after all windows are processed
    label_votes: list[list[str]] = [[] for _ in range(n)]

    window_start = 0
    while window_start < n:
        window_end = min(window_start + window_size, n)
        window_segments = segments[window_start:window_end]
        window_text = " ".join(s.sentence for s in window_segments)

        label, confidence = _classify_text(window_text)
        logger.debug(
            "Window [%d:%d] -> '%s' (confidence=%.3f)",
            window_start, window_end, label, confidence,
        )

        for i in range(window_start, window_end):
            label_votes[i].append(label)

        window_start += step

    # Majority vote per sentence
    provisional: list[str] = []
    for i, votes in enumerate(label_votes):
        if not votes:
            provisional.append(settings.NEWS_CATEGORIES[0])
        else:
            majority = max(set(votes), key=votes.count)
            provisional.append(majority)

    logger.info(
        "Sliding window classification complete. Unique provisional labels: %s",
        list(set(provisional)),
    )
    return provisional


def _detect_and_fix_boundary_misfits(
    segments: list[TranscriptSegment],
    embeddings: np.ndarray,
    provisional_labels: list[str],
) -> list[str]:
    """
    Detect misfit sentences at category boundaries and reassign them.

    Logic:
      - Scan consecutive windows of WINDOW_SIZE sentences.
      - If a window is internally consistent (all same label) but one sentence has
        a cosine similarity to the window mean that is below MISFIT_COSINE_THRESHOLD,
        that sentence is the misfit.
      - The misfit is reassigned by comparing its embedding to the mean embeddings of
        neighboring windows (previous and next) and choosing the closer one's label.
      - This handles the case: Crime, Crime, Sports window -> one Crime sentence
        actually belongs to Sports based on embedding proximity.
    """
    n = len(segments)
    window_size = settings.WINDOW_SIZE
    step = max(1, window_size - settings.WINDOW_OVERLAP)
    refined = provisional_labels.copy()
    threshold = settings.MISFIT_COSINE_THRESHOLD

    window_start = 0
    while window_start + window_size <= n:
        window_end = window_start + window_size
        window_labels = [refined[i] for i in range(window_start, window_end)]

        # Only inspect windows where all labels are the same (internally consistent)
        if len(set(window_labels)) == 1:
            window_embeds = embeddings[window_start:window_end]
            mean_embed = window_embeds.mean(axis=0, keepdims=True)
            sims = cosine_similarity(mean_embed, window_embeds).flatten()

            misfit_idx_local = int(np.argmin(sims))
            misfit_sim = float(sims[misfit_idx_local])

            if misfit_sim < threshold:
                misfit_global_idx = window_start + misfit_idx_local
                misfit_embed = embeddings[misfit_global_idx].reshape(1, -1)

                # Candidate labels from neighboring windows
                neighbor_labels = []
                if window_start > 0:
                    prev_start = max(0, window_start - step)
                    prev_embed = embeddings[prev_start:window_start].mean(axis=0, keepdims=True)
                    sim_prev = float(cosine_similarity(misfit_embed, prev_embed).flatten()[0])
                    neighbor_labels.append((sim_prev, refined[prev_start]))

                if window_end < n:
                    next_end = min(n, window_end + step)
                    next_embed = embeddings[window_end:next_end].mean(axis=0, keepdims=True)
                    sim_next = float(cosine_similarity(misfit_embed, next_embed).flatten()[0])
                    neighbor_labels.append((sim_next, refined[window_end]))

                if neighbor_labels:
                    best_label = max(neighbor_labels, key=lambda x: x[0])[1]
                    old_label = refined[misfit_global_idx]

                    if best_label != old_label:
                        refined[misfit_global_idx] = best_label
                        logger.info(
                            "Misfit detected at sentence %d (sim=%.3f). "
                            "Reassigned: '%s' -> '%s'. Sentence: '%s...'",
                            misfit_global_idx,
                            misfit_sim,
                            old_label,
                            best_label,
                            segments[misfit_global_idx].sentence[:60],
                        )

        window_start += step

    return refined


def _merge_consecutive_same_label(
    segments: list[TranscriptSegment],
    labels: list[str],
) -> list[tuple[str, list[int]]]:
    """
    Merge consecutive segments that share the same category label into groups.
    Returns a list of (category, [sentence_indices]) tuples.
    """
    if not labels:
        return []

    groups: list[tuple[str, list[int]]] = []
    current_label = labels[0]
    current_indices = [0]

    for i in range(1, len(labels)):
        if labels[i] == current_label:
            current_indices.append(i)
        else:
            groups.append((current_label, current_indices))
            current_label = labels[i]
            current_indices = [i]

    groups.append((current_label, current_indices))
    return groups


def _build_cluster_results(
    segments: list[TranscriptSegment],
    embeddings: np.ndarray,
    final_labels: list[str],
) -> tuple[list[ClusterResult], np.ndarray]:
    """
    After category labels are finalized per sentence, merge same-label consecutive
    groups and apply HDBSCAN within each category group to form sub-clusters.

    For short news segments (e.g., 30s video), intra-category HDBSCAN with
    min_cluster_size=2 effectively groups repeated mentions of the same topic.

    Returns (list of ClusterResult, integer label array for metric computation).
    """
    groups = _merge_consecutive_same_label(segments, final_labels)

    # Aggregate all segments of the same category across the full transcript
    category_sentence_map: dict[str, list[int]] = {}
    for category, indices in groups:
        if category not in category_sentence_map:
            category_sentence_map[category] = []
        category_sentence_map[category].extend(indices)

    results: list[ClusterResult] = []
    integer_labels = np.full(len(segments), -1, dtype=int)
    cluster_counter = 0

    for category, indices in category_sentence_map.items():
        cat_embeddings = embeddings[indices]
        cat_segments = [segments[i] for i in indices]

        if len(indices) < settings.HDBSCAN_MIN_CLUSTER_SIZE:
            # Too few sentences for HDBSCAN; treat as a single cluster
            for idx in indices:
                integer_labels[idx] = cluster_counter

            results.append(
                ClusterResult(
                    cluster_id=cluster_counter,
                    category=category,
                    sentences=[s.sentence for s in cat_segments],
                    timestamps=[(s.start_time, s.end_time) for s in cat_segments],
                    confidence=1.0,
                )
            )
            cluster_counter += 1
            continue

        sub_clusterer = hdbscan.HDBSCAN(
            min_cluster_size=settings.HDBSCAN_MIN_CLUSTER_SIZE,
            min_samples=settings.HDBSCAN_MIN_SAMPLES,
            metric="euclidean",
        )
        sub_labels = sub_clusterer.fit_predict(cat_embeddings)

        unique_sub = set(sub_labels)
        unique_sub.discard(-1)

        if not unique_sub:
            # All noise — treat as single group
            for idx in indices:
                integer_labels[idx] = cluster_counter
            results.append(
                ClusterResult(
                    cluster_id=cluster_counter,
                    category=category,
                    sentences=[s.sentence for s in cat_segments],
                    timestamps=[(s.start_time, s.end_time) for s in cat_segments],
                    confidence=0.8,
                )
            )
            cluster_counter += 1
        else:
            for sub_id in sorted(unique_sub):
                sub_mask = sub_labels == sub_id
                sub_seg_indices = [indices[j] for j in range(len(indices)) if sub_mask[j]]
                sub_segments = [segments[i] for i in sub_seg_indices]

                for idx in sub_seg_indices:
                    integer_labels[idx] = cluster_counter

                results.append(
                    ClusterResult(
                        cluster_id=cluster_counter,
                        category=category,
                        sentences=[s.sentence for s in sub_segments],
                        timestamps=[(s.start_time, s.end_time) for s in sub_segments],
                        confidence=0.9,
                    )
                )
                cluster_counter += 1

            # Handle noise sentences within category — assign to nearest sub-cluster
            noise_mask = sub_labels == -1
            noise_local_indices = [j for j in range(len(indices)) if noise_mask[j]]
            for j in noise_local_indices:
                global_idx = indices[j]
                noise_embed = embeddings[global_idx].reshape(1, -1)

                # Find closest non-noise sub-cluster by mean embedding
                best_cluster_id = cluster_counter - 1
                best_sim = -1.0
                for c in results[-len(unique_sub):]:
                    c_embeds = np.array([
                        embeddings[k]
                        for k in range(len(segments))
                        if integer_labels[k] == c.cluster_id
                    ])
                    if len(c_embeds) == 0:
                        continue
                    mean_c = c_embeds.mean(axis=0, keepdims=True)
                    sim = float(cosine_similarity(noise_embed, mean_c).flatten()[0])
                    if sim > best_sim:
                        best_sim = sim
                        best_cluster_id = c.cluster_id

                integer_labels[global_idx] = best_cluster_id
                # Append sentence to the matched cluster
                for c in results:
                    if c.cluster_id == best_cluster_id:
                        c.sentences.append(segments[global_idx].sentence)
                        c.timestamps.append((segments[global_idx].start_time, segments[global_idx].end_time))
                        break

    logger.info(
        "Final cluster count: %d | Categories: %s",
        len(results),
        list(category_sentence_map.keys()),
    )
    return results, integer_labels


def cluster_and_categorize(
    segments: list[TranscriptSegment],
    embeddings: np.ndarray,
    min_cluster_size: int = None,
    min_samples: int = None,
    relabel_map: dict = None,
) -> tuple[list[ClusterResult], np.ndarray, list[str]]:
    """
    Full categorization pipeline (Steps 1-5). Run this ONCE on the first pass.
    Returns a 3-tuple: (clusters, integer_labels, base_refined_labels).

    base_refined_labels are the string labels AFTER sliding-window classification
    and misfit correction but BEFORE any agent relabeling. Cache these and pass
    them to apply_relabel_and_cluster() for fast retries instead of re-running
    the expensive sliding-window zero-shot model.

    Step 1 — Sliding window zero-shot classification (window=3, overlap=1).
    Step 2 — Boundary misfit detection via cosine similarity.
    Step 3 — Apply any relabeling map provided by the LLM Agent.
    Step 4 — Merge consecutive same-label sentences into category groups.
    Step 5 — Intra-category HDBSCAN sub-clustering.
    """
    if min_cluster_size is not None:
        settings.HDBSCAN_MIN_CLUSTER_SIZE = min_cluster_size
    if min_samples is not None:
        settings.HDBSCAN_MIN_SAMPLES = min_samples

    logger.info(
        "Starting categorization pipeline for %d segments "
        "(window=%d, overlap=%d, misfit_threshold=%.2f)",
        len(segments),
        settings.WINDOW_SIZE,
        settings.WINDOW_OVERLAP,
        settings.MISFIT_COSINE_THRESHOLD,
    )

    # Step 1: Sliding window classification
    provisional_labels = _sliding_window_classify(segments)

    # Step 2: Boundary misfit detection and reassignment
    # This is the BASE — cache it for fast retries
    base_refined_labels = _detect_and_fix_boundary_misfits(segments, embeddings, provisional_labels)

    # Step 3: Apply agent relabeling suggestions
    refined_labels = list(base_refined_labels)
    if relabel_map:
        logger.info("Applying agent relabel map: %s", relabel_map)
        refined_labels = [relabel_map.get(lbl, lbl) for lbl in refined_labels]

    # Step 4 & 5: Merge into categories and sub-cluster
    clusters, integer_labels = _build_cluster_results(segments, embeddings, refined_labels)

    return clusters, integer_labels, base_refined_labels


def apply_relabel_and_cluster(
    segments: list[TranscriptSegment],
    embeddings: np.ndarray,
    base_refined_labels: list[str],
    relabel_map: dict = None,
    min_cluster_size: int = None,
    min_samples: int = None,
) -> tuple[list[ClusterResult], np.ndarray]:
    """
    Fast retry path — skips the expensive sliding-window classification.

    Takes the cached base_refined_labels (from the initial cluster_and_categorize call)
    and only re-applies relabeling + HDBSCAN sub-clustering.

    Use this inside the Agent 1 retry loop instead of re-running cluster_and_categorize.
    This avoids ~2 minutes of wasted bart-large-mnli inference per retry.
    """
    if min_cluster_size is not None:
        settings.HDBSCAN_MIN_CLUSTER_SIZE = min_cluster_size
    if min_samples is not None:
        settings.HDBSCAN_MIN_SAMPLES = min_samples

    # Apply cumulative relabel map to the cached base labels
    refined_labels = list(base_refined_labels)
    if relabel_map:
        logger.info("Applying cumulative relabel map: %s", relabel_map)
        refined_labels = [relabel_map.get(lbl, lbl) for lbl in refined_labels]

    # Steps 4 & 5 only: merge + HDBSCAN
    return _build_cluster_results(segments, embeddings, refined_labels)
