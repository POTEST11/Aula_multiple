"""Node 4: Output formatting.

Formats the adapted activity into the final structured output
following the ActivityOutput schema. This node does NOT call
any LLM — it is a pure data transformation/structuring step.
"""

import json
import logging

from app.agent.state import AgentState
from app.schemas.activity import ActivityOutput, CurriculumStandard, VariantOutput

logger = logging.getLogger(__name__)


def _parse_variant_content(raw_content: str) -> dict[str, str]:
    """Parse a variant's raw content string into structured fields.

    The LLM output from previous nodes structures each variant as a JSON
    string with keys "content", "instructions", and "exercises".
    If JSON parsing fails, attempts to split by section headers.
    As last resort, puts everything in content with empty instructions/exercises.

    Args:
        raw_content: The raw variant string (potentially JSON).

    Returns:
        Dict with keys "content", "instructions", "exercises".
    """
    # Try parsing as JSON first
    try:
        text = raw_content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].rstrip()

        data = json.loads(text, strict=False)

        if isinstance(data, dict):
            content = data.get("content", data.get("contenido", ""))
            instructions = data.get("instructions", data.get("instrucciones", ""))
            exercises = data.get("exercises", data.get("ejercicios", ""))

            # Convert lists to strings if the LLM returns arrays
            if isinstance(content, list):
                content = "\n".join(str(item) if isinstance(item, str) else item.get("text", item.get("exercise", str(item))) for item in content)
            if isinstance(instructions, list):
                instructions = "\n".join(str(item) if isinstance(item, str) else item.get("text", item.get("instruction", str(item))) for item in instructions)
            if isinstance(exercises, list):
                exercises = "\n".join(str(item) if isinstance(item, str) else item.get("text", item.get("exercise", str(item))) for item in exercises)

            return {
                "content": content or "",
                "instructions": instructions or "",
                "exercises": exercises or "",
            }
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: use entire text as content — split into thirds if long enough
    text = raw_content.strip()
    if len(text) > 300:
        # Split roughly into content (first half), instructions and exercises
        third = len(text) // 3
        return {
            "content": text[:third].strip(),
            "instructions": text[third:third*2].strip(),
            "exercises": text[third*2:].strip(),
        }

    # Short text: put everything in all fields
    return {
        "content": text,
        "instructions": text,
        "exercises": text,
    }


def _align_standards_to_grade(
    standards: list[CurriculumStandard], grade: int
) -> list[CurriculumStandard]:
    """Filter curriculum standards that match a specific grade.

    Args:
        standards: All curriculum standards from Node 1.
        grade: The grade to filter for.

    Returns:
        List of CurriculumStandard objects matching the grade.
    """
    return [std for std in standards if std.grade == grade]


async def run(state: AgentState) -> dict:
    """Format adapted activity into the final structured output.

    Transforms the adapted anchor activity and variants into the
    ActivityOutput schema with proper structure and metadata.
    This is a pure data transformation node — no LLM calls.

    Args:
        state: Current agent state with adapted activity and variants.

    Returns:
        Partial state update with final_output and current_node.
    """
    # Propagate error from previous nodes
    if state.get("error"):
        return {
            "final_output": None,
            "current_node": "output_formatting",
            "error": state["error"],
        }

    # Validate required inputs
    anchor_activity_adapted = state.get("anchor_activity_adapted")
    variants_adapted = state.get("variants_adapted")

    if not anchor_activity_adapted:
        error_msg = "output_formatting: missing anchor_activity_adapted in state"
        logger.error(error_msg)
        return {
            "final_output": None,
            "current_node": "output_formatting",
            "error": error_msg,
        }

    if not variants_adapted:
        error_msg = "output_formatting: missing variants_adapted in state"
        logger.error(error_msg)
        return {
            "final_output": None,
            "current_node": "output_formatting",
            "error": error_msg,
        }

    # Get curriculum standards for alignment
    curriculum_standards: list[CurriculumStandard] = state.get(
        "curriculum_standards", []
    )

    # Build VariantOutput objects for each grade
    variant_outputs: list[VariantOutput] = []

    for grade, raw_content in variants_adapted.items():
        grade_int = int(grade)

        # Parse the variant content into structured fields
        parsed = _parse_variant_content(raw_content)

        # Align standards to this grade
        aligned_standards = _align_standards_to_grade(
            curriculum_standards, grade_int
        )

        variant_output = VariantOutput(
            grade=grade_int,
            content=parsed["content"],
            instructions=parsed["instructions"],
            exercises=parsed["exercises"],
            aligned_standards=aligned_standards,
        )
        variant_outputs.append(variant_output)

    # Sort variants by grade for consistent output
    variant_outputs.sort(key=lambda v: v.grade)

    # Build the final ActivityOutput
    try:
        final_output = ActivityOutput(
            topic=state["topic"],
            grades=state["grades"],
            subject_name=state["subject"],
            available_resources=state.get("available_resources", []),
            anchor_activity=anchor_activity_adapted,
            variants=variant_outputs,
        )
    except Exception as exc:
        error_msg = f"output_formatting: failed to build ActivityOutput - {exc}"
        logger.error(error_msg, exc_info=True)
        return {
            "final_output": None,
            "current_node": "output_formatting",
            "error": error_msg,
        }

    logger.info(
        "output_formatting: built final output with %d variants for topic='%s'",
        len(variant_outputs),
        state["topic"],
    )

    return {
        "final_output": final_output,
        "current_node": "output_formatting",
    }
