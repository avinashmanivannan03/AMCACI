from pathlib import Path
from TTS.api import TTS

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_tts_model = None


def _load_tts():
    global _tts_model
    if _tts_model is None:
        logger.info("Loading Coqui TTS model: %s", settings.TTS_MODEL)
        _tts_model = TTS(model_name=settings.TTS_MODEL, progress_bar=False)
    return _tts_model


def synthesize(text: str, output_path: str) -> str:
    """
    Convert text to speech using Coqui TTS and save as a WAV file.
    Returns the path to the generated audio file.
    """
    if not text.strip():
        raise ValueError("Empty text passed to TTS engine")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    tts = _load_tts()
    logger.info("Synthesizing TTS for output: %s", output)

    tts.tts_to_file(text=text, file_path=str(output))

    logger.info("TTS audio saved to: %s", output)
    return str(output)


def synthesize_all(summaries: dict[str, str], output_dir: str) -> dict[str, str]:
    """
    Synthesize TTS for all category summaries.
    Returns a dict mapping category name to audio file path.
    """
    output_paths = {}
    for category, summary_text in summaries.items():
        safe_name = category.replace(" ", "_").replace("/", "_").lower()
        file_path = str(Path(output_dir) / f"{safe_name}.wav")
        try:
            synthesize(summary_text, file_path)
            output_paths[category] = file_path
        except Exception as exc:
            logger.error("TTS failed for category '%s': %s", category, exc)
            output_paths[category] = None
    return output_paths

