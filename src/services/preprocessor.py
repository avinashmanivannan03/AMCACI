import numpy as np
import torch
import torchaudio
import noisereduce as nr
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Load Silero VAD model once at module level
_vad_model = None
_vad_utils = None


def _load_vad():
    global _vad_model, _vad_utils
    if _vad_model is None:
        logger.info("Loading Silero VAD model")
        _vad_model, _vad_utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True,
        )
    return _vad_model, _vad_utils


def preprocess_audio(audio_path: str, output_path: str) -> str:
    """
    Apply noise reduction and voice activity detection.
    Returns path to the cleaned audio file containing only voiced segments.
    """
    logger.info("Starting audio preprocessing for: %s", audio_path)

    waveform, sample_rate = torchaudio.load(audio_path)
    audio_np = waveform.squeeze().numpy()

    logger.debug("Applying noise reduction")
    denoised = nr.reduce_noise(y=audio_np, sr=sample_rate, prop_decrease=0.8)

    logger.debug("Running voice activity detection")
    model, utils = _load_vad()
    get_speech_timestamps, _, read_audio, *_ = utils

    audio_tensor = torch.from_numpy(denoised).float()

    speech_timestamps = get_speech_timestamps(
        audio_tensor,
        model,
        sampling_rate=sample_rate,
        threshold=0.5,
        min_speech_duration_ms=200,
        min_silence_duration_ms=300,
    )

    if not speech_timestamps:
        logger.warning("No speech segments detected; using full audio")
        voiced_audio = denoised
    else:
        voiced_segments = [
            denoised[ts["start"]: ts["end"]] for ts in speech_timestamps
        ]
        voiced_audio = np.concatenate(voiced_segments)
        logger.info("VAD retained %d speech segments", len(speech_timestamps))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    voiced_tensor = torch.from_numpy(voiced_audio).unsqueeze(0)
    torchaudio.save(str(output), voiced_tensor, sample_rate)

    logger.info("Preprocessed audio saved to: %s", output)
    return str(output)

