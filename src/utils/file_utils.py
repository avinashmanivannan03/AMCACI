import json
import uuid
from pathlib import Path
from dataclasses import asdict
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_run_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{short_id}"


def ensure_output_dirs(base_dir: Path, run_id: str) -> dict:
    run_dir = base_dir / run_id
    dirs = {
        "root": run_dir,
        "audio": run_dir / "audio",
        "text": run_dir / "text",
        "summaries": run_dir / "summaries",
        "tts": run_dir / "tts",
        "video": run_dir / "video",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    logger.debug("Output directories created at %s", run_dir)
    return dirs


def save_json(data: dict | list, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.debug("Saved JSON to %s", path)


def load_json(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dataclass_to_dict(obj) -> dict | list:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, list):
        return [dataclass_to_dict(i) for i in obj]
    return obj


def save_text(content: str, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.debug("Saved text to %s", path)

