import whisper
from deepmultilingualpunctuation import PunctuationModel
from pathlib import Path
from src.models.schemas import TranscriptSegment
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_whisper_model = None
_punct_model = None


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model: %s", settings.WHISPER_MODEL_SIZE)
        _whisper_model = whisper.load_model(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE
        )
    return _whisper_model


def _load_punct_model():
    global _punct_model
    if _punct_model is None:
        logger.info("Loading punctuation restoration model")
        _punct_model = PunctuationModel()
    return _punct_model


def transcribe(audio_path: str) -> list[TranscriptSegment]:
    """
    Transcribe audio using Whisper with word-level timestamps,
    restore punctuation, and return a list of TranscriptSegment objects.
    """
    logger.info("Transcribing: %s", audio_path)

    model = _load_whisper()
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        fp16=False,
        beam_size=1,
        language="en",
    )

    raw_sentences = []
    for seg in result.get("segments", []):
        raw_sentences.append({
            "text": seg["text"].strip(),
            "start": seg["start"],
            "end": seg["end"],
        })

    logger.info("Whisper produced %d raw segments", len(raw_sentences))

    if not raw_sentences:
        logger.warning("No segments transcribed from audio")
        return []

    punct_model = _load_punct_model()

    segments: list[TranscriptSegment] = []
    for idx, seg in enumerate(raw_sentences):
        punctuated_text = punct_model.restore_punctuation(seg["text"])
        segments.append(
            TranscriptSegment(
                sentence=punctuated_text,
                start_time=seg["start"],
                end_time=seg["end"],
                segment_id=idx,
            )
        )

    logger.info("Transcription complete: %d segments", len(segments))
    return segments

