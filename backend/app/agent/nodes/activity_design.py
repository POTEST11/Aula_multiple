"""Node 2: Activity design.

Generates the anchor activity and grade-specific variant drafts
based on curriculum standards and input parameters using an external LLM.
"""

import asyncio
import json
import logging
from pathlib import Path

import httpx

from app.agent.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "activity_design.txt"


def _load_prompt() -> str:
    """Load the activity design prompt template from disk."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_standards_context(state: AgentState) -> str:
    """Format curriculum standards into a readable context string."""
    standards = state.get("curriculum_standards", [])
    if not standards:
        return "No se encontraron estándares curriculares relevantes."

    lines: list[str] = []
    for std in standards:
        # CurriculumStandard is a Pydantic model; access via attribute or dict
        if hasattr(std, "grade"):
            lines.append(
                f"- Grado {std.grade} | {std.country} | {std.subject}: {std.text}"
            )
        else:
            lines.append(
                f"- Grado {std['grade']} | {std['country']} | {std['subject']}: {std['text']}"
            )
    return "\n".join(lines)


def _build_request_payload(prompt: str, provider: str) -> dict:
    """Build the HTTP request payload based on the LLM provider."""
    if provider == "anthropic":
        return {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
    # Default: OpenAI-compatible (groq, openai, etc.)
    return {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 4096,
    }


def _get_provider_url(provider: str) -> str:
    """Return the API endpoint URL for the given provider."""
    urls = {
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages",
    }
    # Default to groq-style OpenAI-compatible endpoint
    return urls.get(provider, urls["groq"])


def _get_headers(provider: str, api_key: str) -> dict[str, str]:
    """Return authorization headers for the given provider."""
    if provider == "anthropic":
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    # OpenAI-compatible (groq, etc.)
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _extract_text_from_response(response_data: dict, provider: str) -> str:
    """Extract the generated text from the LLM response based on provider."""
    if provider == "anthropic":
        # Anthropic format: {"content": [{"type": "text", "text": "..."}]}
        content_blocks = response_data.get("content", [])
        texts = [b["text"] for b in content_blocks if b.get("type") == "text"]
        return "\n".join(texts)
    # OpenAI-compatible format: {"choices": [{"message": {"content": "..."}}]}
    choices = response_data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def _parse_llm_output(raw_text: str) -> tuple[str, dict[int, str]]:
    """Parse the JSON output from the LLM into anchor and variants.

    Returns:
        Tuple of (anchor_activity_draft, variants_draft).

    Raises:
        ValueError: If the response cannot be parsed.
    """
    # Strip markdown code fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].rstrip()

    data = json.loads(text)

    anchor_activity: str = data.get("anchor_activity", "")
    if not anchor_activity:
        raise ValueError("Missing 'anchor_activity' in LLM response")

    raw_variants = data.get("variants", {})
    if not raw_variants:
        raise ValueError("Missing 'variants' in LLM response")

    # Convert string keys to int
    variants_draft: dict[int, str] = {}
    for grade_key, content in raw_variants.items():
        variants_draft[int(grade_key)] = content

    return anchor_activity, variants_draft


async def run(state: AgentState) -> dict:
    """Design the anchor activity and variant drafts.

    Uses the LLM to generate an anchor activity suitable for all grades,
    then creates initial variant drafts tailored to each specific grade.
    The LLM call is wrapped with asyncio.timeout to enforce the configured
    timeout (default 60s). On timeout, an error is registered in state.

    Args:
        state: Current agent state with curriculum_standards and input fields.

    Returns:
        Partial state update with anchor_activity_draft, variants_draft,
        and current_node.
    """
    settings = get_settings()

    # Build the prompt from template
    prompt_template = _load_prompt()
    standards_context = _build_standards_context(state)
    grades_str = ", ".join(str(g) for g in state["grades"])

    prompt = prompt_template.format(
        topic=state["topic"],
        grades=grades_str,
        subject=state["subject"],
        standards_context=standards_context,
    )

    provider = settings.LLM_PROVIDER
    api_key = settings.LLM_API_KEY
    url = _get_provider_url(provider)
    headers = _get_headers(provider, api_key)
    payload = _build_request_payload(prompt, provider)

    try:
        async with asyncio.timeout(settings.LLM_TIMEOUT_SECONDS):
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS),
                )
                response.raise_for_status()
                response_data = response.json()

    except TimeoutError:
        error_msg = "activity_design: LLM request timed out after {}s".format(
            settings.LLM_TIMEOUT_SECONDS
        )
        logger.error(error_msg)
        return {
            "anchor_activity_draft": None,
            "variants_draft": None,
            "current_node": "activity_design",
            "error": error_msg,
        }
    except httpx.HTTPStatusError as exc:
        error_msg = (
            f"activity_design: LLM API returned status {exc.response.status_code}"
        )
        logger.error(error_msg, exc_info=True)
        return {
            "anchor_activity_draft": None,
            "variants_draft": None,
            "current_node": "activity_design",
            "error": error_msg,
        }
    except Exception as exc:
        error_msg = f"activity_design: {exc}"
        logger.error(error_msg, exc_info=True)
        return {
            "anchor_activity_draft": None,
            "variants_draft": None,
            "current_node": "activity_design",
            "error": error_msg,
        }

    # Parse the LLM response
    try:
        raw_text = _extract_text_from_response(response_data, provider)
        anchor_activity_draft, variants_draft = _parse_llm_output(raw_text)
    except (ValueError, json.JSONDecodeError, KeyError) as exc:
        error_msg = f"activity_design: failed to parse LLM response - {exc}"
        logger.error(error_msg, exc_info=True)
        return {
            "anchor_activity_draft": None,
            "variants_draft": None,
            "current_node": "activity_design",
            "error": error_msg,
        }

    logger.info(
        "activity_design: generated anchor activity + %d variants for topic='%s'",
        len(variants_draft),
        state["topic"],
    )

    return {
        "anchor_activity_draft": anchor_activity_draft,
        "variants_draft": variants_draft,
        "current_node": "activity_design",
    }
