import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.schemas import ClusterResult, SummaryResult
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# API key fetched from settings
GROQ_API_KEY = settings.GROQ_API_KEY

SYSTEM_PROMPT = """You are a professional news summarization agent. You generate concise,
factually accurate, and fluent summaries of news segments. You follow the given instruction
precisely regarding depth and focus. Never add information not present in the source text."""


def _build_summary_prompt(
    category: str,
    sentences: list[str],
    depth_instruction: str,
    custom_note: str = "",
) -> str:
    source = "\n".join(f"- {s}" for s in sentences)
    prompt = (
        f"Category: {category}\n\n"
        f"Source sentences:\n{source}\n\n"
        f"Instruction: {depth_instruction}"
    )
    if custom_note.strip():
        prompt += f"\nAdditional focus requirement: {custom_note.strip()}"
    return prompt


def run_agent2(
    cluster: ClusterResult,
    depth_level: int = 3,
    custom_note: str = "",
    max_tokens: int = None,
) -> SummaryResult:
    """
    Generate a summary for a cluster using Agent 2 (Llama-3.3-70b via Groq).
    Depth level (1-5) controls verbosity. Custom note adds user-specified focus.
    """
    logger.info(
        "Agent 2 invoked for category '%s' (depth=%d)", cluster.category, depth_level
    )

    depth_instruction = settings.DEPTH_INSTRUCTIONS.get(depth_level, settings.DEPTH_INSTRUCTIONS[3])
    token_limit = max_tokens or settings.MAX_SUMMARY_TOKENS

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        temperature=0.3,
        max_tokens=token_limit,
    )

    prompt = _build_summary_prompt(
        category=cluster.category,
        sentences=cluster.sentences,
        depth_instruction=depth_instruction,
        custom_note=custom_note,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    summary_text = response.content.strip()

    from rouge_score import rouge_scorer as rs
    scorer = rs.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    reference = " ".join(cluster.sentences)
    scores = scorer.score(reference, summary_text)
    rouge = {
        "rouge1": round(scores["rouge1"].fmeasure, 4),
        "rouge2": round(scores["rouge2"].fmeasure, 4),
        "rougeL": round(scores["rougeL"].fmeasure, 4),
    }

    logger.info(
        "Agent 2 summary generated for '%s' | ROUGE-L: %.4f",
        cluster.category,
        rouge["rougeL"],
    )

    return SummaryResult(
        category=cluster.category,
        extractive_sentences=cluster.sentences[:3],
        abstractive_summary=summary_text,
        rouge_scores=rouge,
        agent_refined=True,
    )

