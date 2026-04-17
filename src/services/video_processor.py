import cv2
import os
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

from src.models.schemas import ClusterResult, FrameInfo, VideoResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


def merge_segments(chunks: list[dict], gap_threshold: float = 2.0) -> list[tuple[float, float]]:
    """Merge consecutive temporal segments if the gap between them is <= gap_threshold seconds."""
    if not chunks:
        return []

    merged = []
    current_start = chunks[0]["start"]
    current_end   = chunks[0]["end"]

    for i in range(1, len(chunks)):
        if chunks[i]["start"] - current_end <= gap_threshold:
            current_end = max(current_end, chunks[i]["end"])
        else:
            merged.append((current_start, current_end))
            current_start = chunks[i]["start"]
            current_end   = chunks[i]["end"]

    merged.append((current_start, current_end))
    return merged


def match_summary_to_timestamps(cluster: ClusterResult) -> list[dict]:
    """
    Return one clip dict per extractive summary sentence using the pre-aligned
    timestamps from the text pipeline.

      ClusterResult.sentences[i]  ->  ClusterResult.timestamps[i]  (1:1 aligned)

    Only the sentences selected as part of the extractive summary are returned,
    NOT every transcript segment — so the resulting video is a true summary.
    """
    clips = []
    for sent, (start, end) in zip(cluster.sentences, cluster.timestamps):
        clips.append({"start": start, "end": end, "text": sent})
    return clips


def extract_3_frames_per_sentence(
    video_path: str,
    clips: list[dict],
    output_folder: Path,
) -> list[FrameInfo]:
    """
    Primary keyframe method (notebook section: 'frame extraction using summary sentences').

    For each summary-sentence clip extract 3 frames:
        - start  : opening frame
        - mid    : (start + end) / 2
        - end    : end - 0.1 s  (avoids last-frame decode issues)

    Seeks directly into the ORIGINAL video using cv2 frame-number addressing.
    """
    output_folder.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        logger.warning("Could not determine FPS for %s — defaulting to 30", video_path)
        fps = 30.0

    saved_frames: list[FrameInfo] = []

    for i, clip in enumerate(clips):
        start = clip["start"]
        end   = clip["end"]

        times = [
            start,
            (start + end) / 2,
            max(start, end - 0.1),
        ]
        types = ["start", "mid", "end"]

        for j, t in enumerate(times):
            frame_number = int(t * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if ret:
                filename  = f"sent_{i}_frame_{j}_{t:.2f}.jpg"
                file_path = output_folder / filename
                cv2.imwrite(str(file_path), frame)
                saved_frames.append(FrameInfo(
                    frame_path=str(file_path),
                    text=clip["text"],
                    timestamp=t,
                    frame_type=types[j],
                ))
            else:
                logger.warning("Failed to read frame at %.2fs for sentence %d", t, i)

    cap.release()
    logger.info(
        "Keyframes: %d frames from %d sentences -> %s",
        len(saved_frames), len(clips), output_folder,
    )
    return saved_frames


def extract_summary_video(
    video_path: str,
    final_segments: list[tuple[float, float]],
    output_path: Path,
    tts_audio_path: str = None,
) -> str:
    """
    Cut the summary segments from the original video, concatenate them, and replace
    the original audio track with the TTS-synthesised voice.

    Audio replacement rules:
      - Original video audio is stripped from every subclip (without_audio()).
      - If tts_audio_path is provided and the file exists:
          * TTS shorter than video -> video is trimmed to TTS duration
          * TTS longer  than video -> TTS is trimmed to video duration
      - If no TTS is available, the output is muted (silent).
    """
    if not final_segments:
        logger.warning("No segments to extract — skipping %s", output_path)
        return ""

    logger.info(
        "Compiling summary video from %d segment(s) -> %s", len(final_segments), output_path
    )
    tts_audio = None
    try:
        video = VideoFileClip(video_path)
        clips = []

        for start, end in final_segments:
            start = max(0.0, start)
            end   = min(video.duration, end)
            if start >= end:
                continue
            # Strip original audio — TTS voice will be attached after concatenation
            clips.append(video.subclip(start, end).without_audio())

        if not clips:
            video.close()
            return ""

        final = concatenate_videoclips(clips, method="compose")

        # ── Attach TTS audio ───────────────────────────────────────────────────
        if tts_audio_path and Path(tts_audio_path).exists():
            tts_audio = AudioFileClip(tts_audio_path)

            if tts_audio.duration < final.duration:
                # TTS is shorter — trim video to match so there's no silent tail
                logger.info(
                    "TTS (%.1fs) shorter than compiled video (%.1fs) — trimming video",
                    tts_audio.duration, final.duration,
                )
                final = final.subclip(0, tts_audio.duration)
            else:
                # TTS longer or equal — trim audio to video duration
                tts_audio = tts_audio.subclip(0, final.duration)

            final = final.set_audio(tts_audio)
            logger.info("TTS audio successfully attached to video for %s", output_path)
        else:
            logger.warning(
                "No TTS audio available for %s — output will be silent", output_path
            )

        final.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            logger=None,    # suppress moviepy progress bar spam
            threads=4,
        )

        # ── Memory cleanup (important for MoviePy) ─────────────────────────────
        for clip in clips:
            clip.close()
        if tts_audio:
            tts_audio.close()
        final.close()
        video.close()

        logger.info("Summary video written: %s", output_path)
        return str(output_path)

    except Exception as exc:
        logger.error("Failed to compile summary video for %s: %s", output_path, exc)
        return ""


def process_video_pipeline(
    video_path: str,
    clusters: list[ClusterResult],
    output_dir: Path,
    tts_paths: dict[str, str] = None,
) -> dict[str, VideoResult]:
    """
    Main orchestrator.

    For each topic cluster:
      1. Match extractive summary sentences to their aligned timestamps
      2. Deduplicate and sort clips chronologically
      3. Merge nearby clips (gap <= 5 s) into contiguous segments
      4. Build summary video from those segments + replace audio with TTS WAV
      5. Extract 3 keyframes per sentence from the original video

    Args:
        video_path : Original input MP4 path.
        clusters   : ClusterResult list from the text pipeline.
        output_dir : Base output directory for this run's video artefacts.
        tts_paths  : Dict{category -> WAV path} from Stage 7 (tts_engine.synthesize_all).
    """
    results: dict[str, VideoResult] = {}
    tts_paths = tts_paths or {}
    logger.info("Video pipeline started for %d cluster(s)", len(clusters))

    for cluster in clusters:
        category       = cluster.category
        category_clean = category.replace(" ", "_").replace("&", "and")
        tts_wav        = tts_paths.get(category)

        logger.info(
            "Processing '%s' | TTS: %s", category, tts_wav if tts_wav else "none"
        )

        # 1. Map summary sentences -> timestamp clips
        matched_clips = match_summary_to_timestamps(cluster)
        if not matched_clips:
            logger.warning("No clips matched for '%s' — skipping", category)
            continue

        # 2. Deduplicate
        seen: set = set()
        unique_clips: list = []
        for c in matched_clips:
            key = (c["start"], c["end"])
            if key not in seen:
                seen.add(key)
                unique_clips.append(c)

        # 3. Sort chronologically
        sorted_clips = sorted(unique_clips, key=lambda x: x["start"])

        # 4. Merge nearby segments
        final_segments = merge_segments(sorted_clips, gap_threshold=5.0)

        # 5. Compile summary video with TTS audio
        summary_video_path = output_dir / f"{category_clean}_summary.mp4"
        final_video_path = extract_summary_video(
            video_path,
            final_segments,
            summary_video_path,
            tts_audio_path=tts_wav,
        )

        # 6. Extract 3 keyframes per sentence (primary notebook method)
        frames_folder = output_dir / f"{category_clean}_keyframes"
        frames_info = extract_3_frames_per_sentence(
            video_path, sorted_clips, frames_folder
        )

        results[category] = VideoResult(
            category=category,
            summary_video_path=final_video_path,
            keyframes=frames_info,
            segments=final_segments,
        )

    logger.info("Video pipeline complete — %d result(s) produced", len(results))
    return results
