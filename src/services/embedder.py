import numpy as np
from sentence_transformers import SentenceTransformer
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_sbert_model = None


def _load_sbert():
    global _sbert_model
    if _sbert_model is None:
        logger.info("Loading SBERT model: %s", settings.SBERT_MODEL)
        _sbert_model = SentenceTransformer(settings.SBERT_MODEL)
    return _sbert_model


def embed_sentences(sentences: list[str]) -> np.ndarray:
    """
    Encode a list of sentences into dense vector embeddings using SBERT.
    Returns a numpy array of shape (n_sentences, embedding_dim).
    """
    if not sentences:
        raise ValueError("No sentences provided for embedding")

    model = _load_sbert()
    logger.info("Embedding %d sentences", len(sentences))

    embeddings = model.encode(
        sentences,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )

    logger.debug("Embedding shape: %s", embeddings.shape)
    return embeddings

