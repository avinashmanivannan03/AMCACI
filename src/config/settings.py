import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Whisper
    WHISPER_MODEL_SIZE: str = "medium"
    WHISPER_DEVICE: str = "cpu"

    # Embedding
    SBERT_MODEL: str = "all-MiniLM-L6-v2"

    # Zero-shot classification
    ZEROSHOT_MODEL: str = "facebook/bart-large-mnli"

    # News-specific category labels — kept concise for zero-shot performance
    NEWS_CATEGORIES: list = [
        "Sports",
        "Crime",
        "Politics",
        "Business and Finance",
        "Technology",
        "Health",
        "Entertainment",
        "Weather",
        "International Affairs",
        "Education",
    ]

    # Sliding window categorization
    WINDOW_SIZE: int = 3          # Number of sentences per classification window
    WINDOW_OVERLAP: int = 1       # Overlap between consecutive windows
    # Cosine similarity threshold below which a sentence is considered a misfit
    MISFIT_COSINE_THRESHOLD: float = 0.20

    # HDBSCAN — applied after category assignment to cluster within each category group
    HDBSCAN_MIN_CLUSTER_SIZE: int = 2
    HDBSCAN_MIN_SAMPLES: int = 1

    # Agent 1 metric thresholds
    SILHOUETTE_THRESHOLD: float = 0.30
    DBI_THRESHOLD: float = 1.50
    NOISE_PCT_THRESHOLD: float = 30.0
    CV_COHERENCE_THRESHOLD: float = 0.40
    MAX_RECLUSTER_ATTEMPTS: int = 3

    # Summarization
    SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"
    ROUGE_L_THRESHOLD: float = 0.30
    MAX_SUMMARY_TOKENS: int = 180
    MIN_SUMMARY_TOKENS: int = 40

    # TTS
    TTS_MODEL: str = "tts_models/en/ljspeech/tacotron2-DDC"

    # Paths
    BASE_OUTPUT_DIR: Path = Path("data/outputs")
    TEMP_DIR: Path = Path("data/temp")

    # Feedback token budget
    MAX_TOTAL_FEEDBACK_TOKENS: int = 800

    DEPTH_INSTRUCTIONS: dict = {
        1: "Summarize this topic in exactly one brief sentence.",
        2: "Provide a short 2 to 3 sentence summary covering only the main point.",
        3: "Provide a standard balanced summary of 4 to 5 sentences.",
        4: "Provide a detailed paragraph including key facts, context, and relevant figures.",
        5: "Provide a comprehensive, in-depth analysis covering all significant details, background, and implications.",
    }


settings = Settings()
