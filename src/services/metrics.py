import numpy as np
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_mutual_info_score,
    normalized_mutual_info_score,
)
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary
from gensim.utils import simple_preprocess

from src.models.schemas import ClusterResult, MetricScores
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _compute_cv_coherence(cluster: ClusterResult) -> float:
    """
    Compute c_v topic coherence for a single cluster using gensim.
    Returns coherence score, or 0.0 if insufficient data.
    """
    tokenized = [simple_preprocess(s) for s in cluster.sentences]
    tokenized = [t for t in tokenized if t]

    if len(tokenized) < 2:
        return 0.0

    dictionary = Dictionary(tokenized)
    corpus = [dictionary.doc2bow(t) for t in tokenized]

    if len(dictionary) < 3:
        return 0.0

    try:
        from gensim.models import LdaModel
        lda = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=1,
            passes=5,
            random_state=42,
        )
        cm = CoherenceModel(
            model=lda,
            texts=tokenized,
            dictionary=dictionary,
            coherence="c_v",
        )
        score = cm.get_coherence()
        return float(np.clip(score, 0.0, 1.0))
    except Exception as exc:
        logger.warning("Coherence computation failed for cluster %d: %s", cluster.cluster_id, exc)
        return 0.0


def compute_metrics(
    clusters: list[ClusterResult],
    embeddings: np.ndarray,
    labels: np.ndarray,
    prev_labels: np.ndarray = None,
) -> MetricScores:
    """
    Compute all Agent 1 evaluation metrics for the current clustering result.
    """
    non_noise_mask = labels != -1

    failure_reasons: list[str] = []

    if non_noise_mask.sum() < 2 or len(set(labels[non_noise_mask])) < 2:
        logger.warning("Insufficient clusters for metric computation")
        return MetricScores(
            silhouette_overall=0.0,
            dbi=9.99,
            ch_index=0.0,
            noise_pct=100.0,
            per_cluster_coherence={},
            passed=False,
            failure_reasons=["Insufficient clusters for evaluation"],
        )

    valid_embeddings = embeddings[non_noise_mask]
    valid_labels = labels[non_noise_mask]

    silhouette = float(silhouette_score(valid_embeddings, valid_labels))
    dbi = float(davies_bouldin_score(valid_embeddings, valid_labels))
    ch = float(calinski_harabasz_score(valid_embeddings, valid_labels))
    noise_pct = float((np.sum(labels == -1) / len(labels)) * 100)

    per_cluster_coherence = {}
    for cluster in clusters:
        score = _compute_cv_coherence(cluster)
        per_cluster_coherence[cluster.category] = round(score, 4)

    ami, nmi = None, None
    if prev_labels is not None and len(prev_labels) == len(labels):
        ami = float(adjusted_mutual_info_score(prev_labels, labels))
        nmi = float(normalized_mutual_info_score(prev_labels, labels))

    if silhouette < settings.SILHOUETTE_THRESHOLD:
        failure_reasons.append(
            f"Silhouette score {silhouette:.3f} is below threshold {settings.SILHOUETTE_THRESHOLD}"
        )
    if dbi > settings.DBI_THRESHOLD:
        failure_reasons.append(
            f"DBI {dbi:.3f} exceeds threshold {settings.DBI_THRESHOLD}"
        )
    if noise_pct > settings.NOISE_PCT_THRESHOLD:
        failure_reasons.append(
            f"Noise percentage {noise_pct:.1f}% exceeds threshold {settings.NOISE_PCT_THRESHOLD}%"
        )

    low_coherence = [
        f"Cluster '{k}' c_v coherence {v:.3f}"
        for k, v in per_cluster_coherence.items()
        if v < settings.CV_COHERENCE_THRESHOLD
    ]
    if low_coherence:
        failure_reasons.extend(low_coherence)

    passed = len(failure_reasons) == 0

    logger.info(
        "Metrics - Silhouette: %.3f | DBI: %.3f | CH: %.1f | Noise: %.1f%% | Passed: %s",
        silhouette, dbi, ch, noise_pct, passed,
    )

    return MetricScores(
        silhouette_overall=round(silhouette, 4),
        dbi=round(dbi, 4),
        ch_index=round(ch, 4),
        noise_pct=round(noise_pct, 2),
        per_cluster_coherence=per_cluster_coherence,
        ami=round(ami, 4) if ami is not None else None,
        nmi=round(nmi, 4) if nmi is not None else None,
        passed=passed,
        failure_reasons=failure_reasons,
    )

