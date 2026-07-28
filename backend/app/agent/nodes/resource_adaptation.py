"""Node 3: Resource adaptation.

Adapts the activity drafts to incorporate the available resources
specified by the teacher. If no resources are specified, assumes
basic resources (pizarra, cuadernos, lápices).
"""

import asyncio
import json
import logging
from pathlib import Path

import httpx

from app.agent.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)

_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "prompts" / "resource_adaptation.txt"
)

_DEFAULT_RESOURCES = ["pizarra", "cuadernos", "lápices"]


def _load_prompt() -> str:
    """Load the resource adaptation prompt template from disk."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_request_payload(prompt: str, provider: str) -> dict:
    """Build the HTTP request payload based on the LLM provider."""
    if provider == "anthropic":
        return {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
    if provider == "openrouter":
        return {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096,
        }
    # Default: OpenAI-compatible (groq, openai, etc.)
    return {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 4096,
    }


def _get_provider_url(provider: str) -> str:
    """Return the API endpoint URL for the given provider."""
    urls = {
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    }
    return urls.get(provider, urls["groq"])


def _get_headers(provider: str, api_key: str) -> dict[str, str]:
    """Return authorization headers for the given provider."""
    if provider == "anthropic":
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    if provider == "openrouter":
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://aula-multiple.app",
            "X-Title": "Aula Multiple",
        }
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _extract_text_from_response(response_data: dict, provider: str) -> str:
    """Extract the generated text from the LLM response based on provider."""
    if provider == "anthropic":
        content_blocks = response_data.get("content", [])
        texts = [b["text"] for b in content_blocks if b.get("type") == "text"]
        return "\n".join(texts)
    choices = response_data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def _parse_llm_output(raw_text: str) -> tuple[str, dict[int, str]]:
    """Parse the JSON output from the LLM into adapted anchor and variants.

    Returns:
        Tuple of (anchor_activity_adapted, variants_adapted).

    Raises:
        ValueError: If the response cannot be parsed.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].rstrip()

    import re

    # Fix invalid escape sequences from LLM output
    text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)

    data = json.loads(text, strict=False)

    anchor_activity: str = data.get("anchor_activity", "")
    if not anchor_activity:
        raise ValueError("Missing 'anchor_activity' in LLM response")

    raw_variants = data.get("variants", {})
    if not raw_variants:
        raise ValueError("Missing 'variants' in LLM response")

    variants_adapted: dict[int, str] = {}
    for grade_key, content in raw_variants.items():
        if isinstance(content, dict):
            variants_adapted[int(grade_key)] = json.dumps(content, ensure_ascii=False)
        else:
            variants_adapted[int(grade_key)] = content

    return anchor_activity, variants_adapted


def _format_variants_for_prompt(variants: dict[int, str] | None) -> str:
    """Format variants dict into a readable string for the prompt."""
    if not variants:
        return "No hay variantes disponibles."
    lines: list[str] = []
    for grade, content in variants.items():
        lines.append(f"--- Grado {grade} ---\n{content}")
    return "\n\n".join(lines)


async def run(state: AgentState) -> dict:
    """Adapt activity drafts to available resources.

    Nodo 3: Adapta las instrucciones de la actividad según los recursos
    disponibles del docente. Si no hay recursos especificados, asume básicos
    (pizarra, cuadernos, lápices).

    This is a second independent LLM call (separate from Node 2), with its
    own 60s timeout applied individually.

    Input: state.anchor_activity_draft, state.variants_draft, state.available_resources
    Output: state.anchor_activity_adapted, state.variants_adapted

    Args:
        state: Current agent state with drafts and available_resources.

    Returns:
        Partial state update with anchor_activity_adapted, variants_adapted,
        and current_node.
    """
    # Propagate error from previous nodes without calling LLM
    if state.get("error"):
        return {
            "anchor_activity_adapted": None,
            "variants_adapted": None,
            "current_node": "resource_adaptation",
            "error": state["error"],
        }

    settings = get_settings()

    # Determine available resources (default to basic if empty/None)
    available_resources = state.get("available_resources") or []
    if not available_resources:
        available_resources = _DEFAULT_RESOURCES

    # Build the prompt
    prompt_template = _load_prompt()
    grades_str = ", ".join(str(g) for g in state["grades"])
    variants_str = _format_variants_for_prompt(state.get("variants_draft"))
    resources_str = ", ".join(available_resources)

    prompt = prompt_template.format(
        anchor_activity=state.get("anchor_activity_draft", ""),
        variants=variants_str,
        resources=resources_str,
        topic=state["topic"],
        grades=grades_str,
    )

    provider = settings.LLM_PROVIDER
    api_key = settings.LLM_API_KEY
    url = _get_provider_url(provider)
    headers = _get_headers(provider, api_key)
    payload = _build_request_payload(prompt, provider)

    max_retries = 3
    response_data = None

    try:
        async with asyncio.timeout(settings.LLM_TIMEOUT_SECONDS):
            async with httpx.AsyncClient() as client:
                for attempt in range(max_retries):
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS),
                    )
                    response.raise_for_status()
                    response_data = response.json()

                    # Check if response has content
                    raw_text = _extract_text_from_response(response_data, provider)
                    if raw_text and raw_text.strip():
                        break
                    logger.warning(
                        "resource_adaptation: empty response on attempt %d/%d, retrying...",
                        attempt + 1, max_retries,
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 * (attempt + 1))

    except TimeoutError:
        error_msg = "resource_adaptation: LLM request timed out after {}s".format(
            settings.LLM_TIMEOUT_SECONDS
        )
        logger.error(error_msg)
        return {
            "anchor_activity_adapted": None,
            "variants_adapted": None,
            "current_node": "resource_adaptation",
            "error": error_msg,
        }
    except httpx.HTTPStatusError as exc:
        error_msg = (
            f"resource_adaptation: LLM API returned status {exc.response.status_code}"
        )
        logger.error(error_msg, exc_info=True)
        return {
            "anchor_activity_adapted": None,
            "variants_adapted": None,
            "current_node": "resource_adaptation",
            "error": error_msg,
        }
    except Exception as exc:
        error_msg = f"resource_adaptation: {exc}"
        logger.error(error_msg, exc_info=True)
        return {
            "anchor_activity_adapted": None,
            "variants_adapted": None,
            "current_node": "resource_adaptation",
            "error": error_msg,
        }

    # Parse the LLM response
    try:
        raw_text = _extract_text_from_response(response_data, provider)
        anchor_activity_adapted, variants_adapted = _parse_llm_output(raw_text)
    except (ValueError, json.JSONDecodeError, KeyError) as exc:
        error_msg = f"resource_adaptation: failed to parse LLM response - {exc}"
        logger.error(error_msg, exc_info=True)
        return {
            "anchor_activity_adapted": None,
            "variants_adapted": None,
            "current_node": "resource_adaptation",
            "error": error_msg,
        }

    logger.info(
        "resource_adaptation: adapted activity for resources=[%s], topic='%s'",
        resources_str,
        state["topic"],
    )

    return {
        "anchor_activity_adapted": anchor_activity_adapted,
        "variants_adapted": variants_adapted,
        "current_node": "resource_adaptation",
    }
