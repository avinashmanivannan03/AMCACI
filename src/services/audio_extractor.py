import subprocess
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_audio(video_path: str, output_path: str) -> str:
    """
    Extract audio from a video file as a mono 16kHz WAV using ffmpeg.
    Returns the path to the extracted audio file.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ac", "1",
        "-ar", "16000",
        "-vn",
        "-acodec", "pcm_s16le",
        str(output),
    ]

    logger.info("Extracting audio from: %s", video_path)

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        logger.error("ffmpeg failed: %s", result.stderr)
        raise RuntimeError(f"Audio extraction failed: {result.stderr}")

    logger.info("Audio extracted to: %s", output)
    return str(output)

