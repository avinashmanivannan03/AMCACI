import sys
import json
from pathlib import Path
from src.handlers.pipeline_handler import PipelineHandler
from src.utils.logger import get_logger

logger = get_logger("main")


def cli_callback(step: str, data: dict):
    logger.info("[PIPELINE] %s | %s", step, json.dumps(data, default=str)[:200])


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_video>")
        sys.exit(1)

    video_path = sys.argv[1]
    if not Path(video_path).exists():
        logger.error("Video file not found: %s", video_path)
        sys.exit(1)

    handler = PipelineHandler(progress_callback=cli_callback)
    state = handler.run(video_path)

    if state.completed:
        logger.info("Pipeline finished successfully. Run ID: %s", state.run_id)
    else:
        logger.error("Pipeline did not complete. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

