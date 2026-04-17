import numpy as np
from transformers import pipeline as hf_pipeline
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rouge_score import rouge_scorer

from src.models.schemas import ClusterResult, SummaryResult
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_summarization_model = None
_sbert_for_summary = None


def _load_summarizer():
    global _summarization_model
    if _summarization_model is None:
        logger.info("Loading abstractive summarization model: %s", settings.SUMMARIZATION_MODEL)
        _summarization_model = hf_pipeline(
            "summarization",
            model=settings.SUMMARIZATION_MODEL,
            device=-1,
        )
    return _summarization_model


def _load_sbert():
    global _sbert_for_summary
    if _sbert_for_summary is None:
        _sbert_for_summary = SentenceTransformer(settings.SBERT_MODEL)
    return _sbert_for_summary


def _extractive_summary(sentences: list[str], top_k: int = 3) -> list[str]:
    """
    Select top-k sentences based on cosine similarity to the mean cluster embedding.
    """
    if len(sentences) <= top_k:
        return sentences

    model = _load_sbert()
    embeddings = model.encode(sentences, normalize_embeddings=True)
    mean_vec = embeddings.mean(axis=0, keepdims=True)
    scores = cosine_similarity(mean_vec, embeddings).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]
    top_indices_sorted = sorted(top_indices)
    return [sentences[i] for i in top_indices_sorted]


def _compute_rouge(hypothesis: str, reference: str) -> dict:
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return {
        "rouge1": round(scores["rouge1"].fmeasure, 4),
        "rouge2": round(scores["rouge2"].fmeasure, 4),
        "rougeL": round(scores["rougeL"].fmeasure, 4),
    }


def summarize_cluster(cluster: ClusterResult) -> SummaryResult:
    """
    Perform extractive then abstractive summarization for a single cluster.
    """
    logger.info("Summarizing cluster: %s (%d sentences)", cluster.category, len(cluster.sentences))

    extracted = _extractive_summary(cluster.sentences, top_k=min(3, len(cluster.sentences)))
    extracted_text = " ".join(extracted)

    summarizer = _load_summarizer()
    input_length = len(extracted_text.split())
    max_new = min(settings.MAX_SUMMARY_TOKENS, max(settings.MIN_SUMMARY_TOKENS, input_length // 2))

    try:
        result = summarizer(
            extracted_text,
            max_length=max_new,
            min_length=settings.MIN_SUMMARY_TOKENS,
            do_sample=False,
            truncation=True,
        )
        abstractive = result[0]["summary_text"]
    except Exception as exc:
        logger.warning("Abstractive summarizer failed for '%s': %s", cluster.category, exc)
        abstractive = extracted_text

    rouge = _compute_rouge(abstractive, " ".join(cluster.sentences))
    logger.debug("ROUGE-L for '%s': %.4f", cluster.category, rouge["rougeL"])

    return SummaryResult(
        category=cluster.category,
        extractive_sentences=extracted,
        abstractive_summary=abstractive,
        rouge_scores=rouge,
        agent_refined=False,
    )

