from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TranscriptSegment:
    sentence: str
    start_time: float
    end_time: float
    segment_id: int


@dataclass
class ClusterResult:
    cluster_id: int
    category: str
    sentences: list[str]
    timestamps: list[tuple[float, float]]
    confidence: float


@dataclass
class MetricScores:
    silhouette_overall: float
    dbi: float
    ch_index: float
    noise_pct: float
    per_cluster_coherence: dict[str, float]
    ami: Optional[float] = None
    nmi: Optional[float] = None
    passed: bool = False
    failure_reasons: list[str] = field(default_factory=list)


@dataclass
class SummaryResult:
    category: str
    extractive_sentences: list[str]
    abstractive_summary: str
    rouge_scores: dict[str, float]
    agent_refined: bool = False


@dataclass
class FrameInfo:
    frame_path: str
    text: str
    timestamp: float
    frame_type: str  # "start", "mid", or "end"


@dataclass
class VideoResult:
    category: str
    summary_video_path: str
    keyframes: list[FrameInfo]
    segments: list[tuple[float, float]]


@dataclass
class PipelineState:
    run_id: str
    video_path: str
    audio_path: Optional[str] = None
    transcript: Optional[list[TranscriptSegment]] = None
    clusters: Optional[list[ClusterResult]] = None
    metrics: Optional[MetricScores] = None
    summaries: Optional[list[SummaryResult]] = None
    tts_audio_paths: Optional[dict[str, str]] = None
    video_results: dict[str, VideoResult] = field(default_factory=dict)
    recluster_count: int = 0
    completed: bool = False

