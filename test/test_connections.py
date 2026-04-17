"""
Standalone connection and model sanity tests.
Run directly: python test/test_connections.py
"""

import os
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.utils.logger import get_logger

logger = get_logger("test_connections")

# API key fetched from environment check
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def test_groq_connection():
    logger.info("Testing Groq LLM connection")
    
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage

        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=64,
        )
        response = llm.invoke([HumanMessage(content="Say the word CONNECTED in all caps only.")])
        logger.info("Groq response: %s", response.content.strip())
        assert "CONNECTED" in response.content.upper(), "Unexpected response from Groq"
        logger.info("Groq connection: PASSED")
        return True
    except Exception as exc:
        logger.error("Groq connection FAILED: %s", exc)
        return False


def test_whisper_load():
    logger.info("Testing Whisper model load")
    try:
        import whisper
        model = whisper.load_model("medium", device="cpu")
        assert model is not None
        logger.info("Whisper model load: PASSED")
        return True
    except Exception as exc:
        logger.error("Whisper load FAILED: %s", exc)
        return False


def test_sbert_load():
    logger.info("Testing SBERT model load")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vec = model.encode(["Test sentence for SBERT"], normalize_embeddings=True)
        assert vec.shape[0] == 1
        logger.info("SBERT load and encode: PASSED")
        return True
    except Exception as exc:
        logger.error("SBERT load FAILED: %s", exc)
        return False


def test_zeroshot_classifier():
    logger.info("Testing zero-shot classifier load")
    try:
        from transformers import pipeline
        clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)
        result = clf("The team scored a winning goal.", candidate_labels=["Sports", "Politics"])
        logger.info("Zero-shot top label: %s", result["labels"][0])
        logger.info("Zero-shot classifier: PASSED")
        return True
    except Exception as exc:
        logger.error("Zero-shot classifier FAILED: %s", exc)
        return False


def test_groq_streaming():
    logger.info("Testing Groq streaming response")
    
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Count from 1 to 5, one per line."}],
            stream=True,
            max_tokens=64,
        )
        collected = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            collected += delta
        logger.info("Streamed response: %s", collected.strip())
        logger.info("Groq streaming: PASSED")
        return True
    except Exception as exc:
        logger.error("Groq streaming FAILED: %s", exc)
        return False


if __name__ == "__main__":
    results = {
        "groq_connection": test_groq_connection(),
        "groq_streaming": test_groq_streaming(),
        "whisper_load": test_whisper_load(),
        "sbert_load": test_sbert_load(),
        "zeroshot_classifier": test_zeroshot_classifier(),
    }

    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {name:<30} {status}")
    print("=" * 50)

    if not all(results.values()):
        sys.exit(1)

