import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.schemas import ClusterResult, MetricScores
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# API key fetched from settings
GROQ_API_KEY = settings.GROQ_API_KEY

SYSTEM_PROMPT = """You are a clustering quality analyst for a news transcript pipeline.
You receive clustering metrics and cluster contents, and you diagnose problems and suggest
precise, actionable improvements. Respond only in valid JSON."""

DIAGNOSIS_TEMPLATE = """
Current clustering metrics:
- Silhouette Score: {silhouette}
- Davies-Bouldin Index: {dbi}
- Calinski-Harabasz Index: {ch}
- Noise Percentage: {noise_pct}%
- Per-cluster coherence: {coherence}

Failure reasons identified:
{failure_reasons}

Current clusters and their content:
{cluster_summary}

Available news categories:
{categories}

Respond in this exact JSON format:
{{
  "diagnosis": "<one paragraph explaining the root cause>",
  "suggested_action": "merge_clusters | split_cluster | adjust_parameters | relabel",
  "merge_pairs": [["Category A", "Category B"]],
  "relabel_suggestions": {{"old_label": "new_label"}},
  "new_min_cluster_size": <integer or null>,
  "new_min_samples": <integer or null>,
  "rationale": "<brief rationale for each change>"
}}
"""


def _build_cluster_summary(clusters: list[ClusterResult]) -> str:
    summary = {}
    for c in clusters:
        summary[c.category] = c.sentences[:3]
    return json.dumps(summary, indent=2)


def run_agent1(
    clusters: list[ClusterResult],
    metrics: MetricScores,
    current_min_cluster_size: int,
    current_min_samples: int,
) -> dict:
    """
    Invoke Agent 1 (Llama-3.3-70b via Groq) to diagnose poor clustering
    and return actionable refinement instructions.
    """
    logger.info("Agent 1 invoked for clustering diagnosis")

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        temperature=0.2,
        max_tokens=1024,
    )

    # Handle None values safely
    coherence_data = metrics.per_cluster_coherence if metrics.per_cluster_coherence else {}
    failure_reasons = metrics.failure_reasons if metrics.failure_reasons else []

    prompt = DIAGNOSIS_TEMPLATE.format(
        silhouette=metrics.silhouette_overall if metrics.silhouette_overall is not None else 0.0,
        dbi=metrics.dbi if metrics.dbi is not None else 0.0,
        ch=metrics.ch_index if metrics.ch_index is not None else 0.0,
        noise_pct=metrics.noise_pct if metrics.noise_pct is not None else 0.0,
        coherence=json.dumps(coherence_data),
        failure_reasons="\n".join(f"- {r}" for r in failure_reasons),
        cluster_summary=_build_cluster_summary(clusters),
        categories=", ".join(settings.NEWS_CATEGORIES),
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    logger.debug("Sending diagnosis request to Groq")
    try:
        response = llm.invoke(messages)
        raw_content = response.content.strip()
    except Exception as e:
        logger.error(f"Failed to get response from Groq: {e}")
        return {
            "diagnosis": "Failed to communicate with LLM",
            "suggested_action": "adjust_parameters",
            "new_min_cluster_size": min(current_min_cluster_size + 1, 5),
            "new_min_samples": current_min_samples,
            "merge_pairs": [],
            "relabel_suggestions": {},
            "rationale": "Fallback due to LLM communication error",
        }

    try:
        # Extract JSON if wrapped in code fences
        if "```" in raw_content:
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]

        result = json.loads(raw_content)
        # Normalise None / null fields returned by the LLM to safe empty defaults
        result.setdefault("merge_pairs", [])
        result.setdefault("relabel_suggestions", {})
        result.setdefault("failure_reasons", [])
        if result.get("merge_pairs") is None:
            result["merge_pairs"] = []
        if result.get("relabel_suggestions") is None:
            result["relabel_suggestions"] = {}
        logger.info("Agent 1 suggested action: %s", result.get("suggested_action"))
        return result
    except json.JSONDecodeError as exc:
        logger.error("Agent 1 returned invalid JSON: %s | Raw: %s", exc, raw_content[:300])
        return {
            "diagnosis": "Agent returned malformed response",
            "suggested_action": "adjust_parameters",
            "new_min_cluster_size": min(current_min_cluster_size + 1, 5),
            "new_min_samples": current_min_samples,
            "merge_pairs": [],
            "relabel_suggestions": {},
            "rationale": "Fallback parameter adjustment due to parse failure",
        }

