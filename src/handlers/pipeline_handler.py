import numpy as np
from pathlib import Path
from dataclasses import asdict

from src.config.settings import settings
from src.models.schemas import PipelineState, MetricScores
from src.services.audio_extractor import extract_audio
from src.services.preprocessor import preprocess_audio
from src.services.transcriber import transcribe
from src.services.embedder import embed_sentences
from src.services.clusterer import cluster_and_categorize, apply_relabel_and_cluster
from src.services.metrics import compute_metrics
from src.services.agent1 import run_agent1
from src.services.summarizer import summarize_cluster
from src.services.agent2 import run_agent2
from src.services.tts_engine import synthesize_all
from src.services.video_processor import process_video_pipeline
from src.utils.file_utils import (
    generate_run_id,
    ensure_output_dirs,
    save_json,
    dataclass_to_dict,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineHandler:
    """
    Orchestrates the full AMCACI text pipeline from video input to TTS output.
    Accepts an optional callback for streaming step updates to the UI.
    """

    def __init__(self, progress_callback=None):
        self.callback = progress_callback or (lambda step, data: None)

    def _emit(self, step: str, data: dict):
        logger.debug("Pipeline step: %s | %s", step, data)
        self.callback(step, data)

    def run(self, video_path: str, feedback: dict = None) -> PipelineState:
        run_id = generate_run_id()
        dirs = ensure_output_dirs(settings.BASE_OUTPUT_DIR, run_id)
        state = PipelineState(run_id=run_id, video_path=video_path)

        logger.info("Pipeline started | run_id=%s | video=%s", run_id, video_path)
        self._emit("pipeline_start", {"run_id": run_id})

        # Stage 1: Audio extraction
        self._emit("stage_start", {"stage": "audio_extraction"})
        raw_audio = str(dirs["audio"] / "raw.wav")
        extract_audio(video_path, raw_audio)
        self._emit("stage_complete", {"stage": "audio_extraction", "output": raw_audio})

        # Stage 2: Preprocessing
        self._emit("stage_start", {"stage": "preprocessing"})
        clean_audio = str(dirs["audio"] / "clean.wav")
        preprocess_audio(raw_audio, clean_audio)
        state.audio_path = clean_audio
        self._emit("stage_complete", {"stage": "preprocessing", "output": clean_audio})

        # Stage 3: Transcription
        self._emit("stage_start", {"stage": "transcription"})
        segments = transcribe(clean_audio)
        state.transcript = segments
        transcript_data = [asdict(s) for s in segments]
        save_json(transcript_data, dirs["text"] / "transcript.json")
        self._emit("stage_complete", {
            "stage": "transcription",
            "count": len(segments),
            "data": transcript_data,
        })

        if not segments:
            logger.error("Transcription returned no segments; aborting pipeline")
            return state

        sentences = [s.sentence for s in segments]

        # Stage 4: Embedding + Sliding Window Categorization + HDBSCAN sub-clustering
        self._emit("stage_start", {"stage": "clustering"})
        embeddings = embed_sentences(sentences)

        min_cls = settings.HDBSCAN_MIN_CLUSTER_SIZE
        min_smp = settings.HDBSCAN_MIN_SAMPLES

        # cluster_and_categorize returns (clusters, integer_labels, base_refined_labels)
        clusters, labels, base_labels = cluster_and_categorize(segments, embeddings, min_cls, min_smp)

        cluster_data = [asdict(c) for c in clusters]
        save_json(cluster_data, dirs["text"] / "clusters.json")
        self._emit("stage_complete", {
            "stage": "clustering",
            "num_clusters": len(clusters),
            "data": cluster_data,
        })

        state.clusters = clusters

        # Stage 5: Agent 1 evaluation loop
        prev_labels = None
        # Accumulate relabel suggestions across all attempts so prior relabels persist
        cumulative_relabel: dict = {}
        # Track previous metric signature to detect frozen (unchanging) scores
        prev_score_sig: tuple | None = None

        for attempt in range(settings.MAX_RECLUSTER_ATTEMPTS):
            self._emit("stage_start", {"stage": "agent1_eval", "attempt": attempt + 1})
            metrics = compute_metrics(clusters, embeddings, labels, prev_labels)
            state.metrics = metrics
            metrics_dict = asdict(metrics)
            self._emit("metrics_computed", {"metrics": metrics_dict, "attempt": attempt + 1})

            if metrics.passed:
                logger.info("Clustering passed evaluation on attempt %d", attempt + 1)
                self._emit("agent1_passed", {"attempt": attempt + 1})
                break

            # Early-exit: if scores are mathematically identical to the previous
            # attempt, further retries cannot improve them (frozen geometry).
            current_score_sig = (
                round(metrics.silhouette_overall or 0, 6),
                round(metrics.dbi or 0, 6),
                round(metrics.ch_index or 0, 6),
            )
            if prev_score_sig is not None and current_score_sig == prev_score_sig:
                logger.warning(
                    "Scores identical to previous attempt on attempt %d — "
                    "geometry is frozen, stopping retry loop early.",
                    attempt + 1,
                )
                self._emit("agent1_stalled", {
                    "attempt": attempt + 1,
                    "reason": "Scores unchanged — clustering geometry is frozen.",
                })
                break
            prev_score_sig = current_score_sig

            logger.warning(
                "Clustering failed evaluation (attempt %d). Failures: %s",
                attempt + 1,
                metrics.failure_reasons,
            )
            self._emit("agent1_diagnosis_start", {
                "attempt": attempt + 1,
                "failures": metrics.failure_reasons,
            })

            instructions = run_agent1(clusters, metrics, min_cls, min_smp)
            self._emit("agent1_instructions", {"instructions": instructions, "attempt": attempt + 1})

            # --- Apply parameter changes suggested by agent ---
            if instructions.get("new_min_cluster_size"):
                min_cls = int(instructions["new_min_cluster_size"])
            if instructions.get("new_min_samples"):
                min_smp = int(instructions["new_min_samples"])

            # --- Accumulate relabel_suggestions into cumulative map ---
            for old_lbl, new_lbl in (instructions.get("relabel_suggestions") or {}).items():
                # Transitively update any existing keys that pointed to old_lbl
                for k in list(cumulative_relabel.keys()):
                    if cumulative_relabel[k] == old_lbl:
                        cumulative_relabel[k] = new_lbl
                cumulative_relabel[old_lbl] = new_lbl

            # --- Convert merge_pairs into relabel entries ---
            # merge_pairs: [["A", "B"]] means merge B into A (keep A label)
            for pair in (instructions.get("merge_pairs") or []):
                if len(pair) == 2:
                    keep_lbl, drop_lbl = pair[0], pair[1]
                    # Transitively update
                    for k in list(cumulative_relabel.keys()):
                        if cumulative_relabel[k] == drop_lbl:
                            cumulative_relabel[k] = keep_lbl
                    cumulative_relabel[drop_lbl] = keep_lbl
                    logger.info(
                        "merge_pairs: merging cluster '%s' into '%s'", drop_lbl, keep_lbl
                    )

            prev_labels = labels.copy()

            # --- Fast retry: skip sliding-window, only re-run HDBSCAN ---
            clusters, labels = apply_relabel_and_cluster(
                segments, embeddings, base_labels,
                relabel_map=cumulative_relabel if cumulative_relabel else None,
                min_cluster_size=min_cls,
                min_samples=min_smp,
            )

            state.recluster_count = attempt + 1
            state.clusters = clusters
            self._emit("reclustered", {
                "attempt": attempt + 1,
                "num_clusters": len(clusters),
                "relabel_map": cumulative_relabel,
            })

        # Stage 6: Summarization
        self._emit("stage_start", {"stage": "summarization"})
        summaries = []
        feedback = feedback or {}

        for cluster in clusters:
            depth = int(feedback.get(cluster.category, {}).get("depth", 3))
            custom_note = feedback.get(cluster.category, {}).get("note", "")
            token_budget = _compute_token_budget(feedback, cluster.category)

            summary = summarize_cluster(cluster)

            needs_agent = (
                summary.rouge_scores["rougeL"] < settings.ROUGE_L_THRESHOLD
                or depth != 3
                or bool(custom_note.strip())
            )

            if needs_agent:
                logger.info(
                    "Invoking Agent 2 for '%s' (rougeL=%.4f, depth=%d)",
                    cluster.category,
                    summary.rouge_scores["rougeL"],
                    depth,
                )
                self._emit("agent2_invoked", {"category": cluster.category, "depth": depth})
                summary = run_agent2(
                    cluster,
                    depth_level=depth,
                    custom_note=custom_note,
                    max_tokens=token_budget,
                )

            summaries.append(summary)
            self._emit("summary_ready", {
                "category": cluster.category,
                "summary": summary.abstractive_summary,
                "rouge": summary.rouge_scores,
                "agent_refined": summary.agent_refined,
            })

        state.summaries = summaries
        summary_data = [asdict(s) for s in summaries]
        save_json(summary_data, dirs["summaries"] / "summaries.json")
        self._emit("stage_complete", {"stage": "summarization", "data": summary_data})

        # Stage 7: TTS
        self._emit("stage_start", {"stage": "tts"})
        summary_texts = {s.category: s.abstractive_summary for s in summaries}
        tts_paths = synthesize_all(summary_texts, str(dirs["tts"]))
        state.tts_audio_paths = tts_paths
        self._emit("stage_complete", {"stage": "tts", "paths": tts_paths})

        # Stage 8: Video Processing
        self._emit("stage_start", {"stage": "video_processing"})
        video_output_dir = dirs["video"]
        video_results = process_video_pipeline(
            video_path,
            clusters,
            video_output_dir,
            tts_paths=tts_paths,   # replace original audio with TTS voice
        )
        state.video_results = video_results
        self._emit("stage_complete", {
            "stage": "video_processing",
            "categories": list(video_results.keys()),
            "results": {k: dataclass_to_dict(v) for k, v in video_results.items()}
        })

        state.completed = True
        logger.info("Pipeline complete | run_id=%s", run_id)
        self._emit("pipeline_complete", {"run_id": run_id, "state": dataclass_to_dict(state)})

        return state


def _compute_token_budget(feedback: dict, category: str) -> int:
    """
    Compute per-category token budget proportional to user-assigned depth level.
    Ensures total tokens across all categories does not exceed the global cap.
    """
    if not feedback:
        return settings.MAX_SUMMARY_TOKENS

    total_weight = sum(
        int(v.get("depth", 3)) for v in feedback.values()
    ) or 1
    category_depth = int(feedback.get(category, {}).get("depth", 3))
    ratio = category_depth / total_weight
    budget = int(ratio * settings.MAX_TOTAL_FEEDBACK_TOKENS)
    return max(budget, 60)
