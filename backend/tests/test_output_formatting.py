"""Unit tests for Node 4: Output formatting."""

import json

import pytest

from app.agent.nodes.output_formatting import run, _parse_variant_content, _align_standards_to_grade
from app.schemas.activity import ActivityOutput, CurriculumStandard, VariantOutput


class TestParseVariantContent:
    """Tests for _parse_variant_content helper."""

    def test_parses_valid_json_with_content_fields(self):
        raw = json.dumps({
            "content": "Actividad sobre fracciones",
            "instructions": "Dividir en grupos",
            "exercises": "Ejercicio 1: resolver 1/2 + 1/4",
        })
        result = _parse_variant_content(raw)
        assert result["content"] == "Actividad sobre fracciones"
        assert result["instructions"] == "Dividir en grupos"
        assert result["exercises"] == "Ejercicio 1: resolver 1/2 + 1/4"

    def test_parses_json_with_spanish_keys(self):
        raw = json.dumps({
            "contenido": "Actividad sobre geometría",
            "instrucciones": "Usar regla y compás",
            "ejercicios": "Dibujar un triángulo",
        })
        result = _parse_variant_content(raw)
        assert result["content"] == "Actividad sobre geometría"
        assert result["instructions"] == "Usar regla y compás"
        assert result["exercises"] == "Dibujar un triángulo"

    def test_strips_markdown_code_fences(self):
        raw = '```json\n{"content": "Texto", "instructions": "Inst", "exercises": "Ej"}\n```'
        result = _parse_variant_content(raw)
        assert result["content"] == "Texto"
        assert result["instructions"] == "Inst"
        assert result["exercises"] == "Ej"

    def test_fallback_when_not_json(self):
        raw = "Este es contenido en texto plano sin formato JSON"
        result = _parse_variant_content(raw)
        assert result["content"] == raw
        assert "indicaciones" in result["instructions"].lower() or len(result["instructions"]) > 0
        assert len(result["exercises"]) > 0

    def test_fallback_when_json_is_not_dict(self):
        raw = json.dumps(["lista", "de", "cosas"])
        result = _parse_variant_content(raw)
        assert result["content"] == raw


class TestAlignStandardsToGrade:
    """Tests for _align_standards_to_grade helper."""

    def test_returns_matching_standards(self):
        standards = [
            CurriculumStandard(country="CO", grade=3, subject="Matemáticas", text="Estándar 3"),
            CurriculumStandard(country="CO", grade=5, subject="Matemáticas", text="Estándar 5"),
            CurriculumStandard(country="CO", grade=3, subject="Matemáticas", text="Otro estándar 3"),
        ]
        result = _align_standards_to_grade(standards, 3)
        assert len(result) == 2
        assert all(s.grade == 3 for s in result)

    def test_returns_empty_when_no_match(self):
        standards = [
            CurriculumStandard(country="CO", grade=5, subject="Matemáticas", text="Estándar 5"),
        ]
        result = _align_standards_to_grade(standards, 3)
        assert result == []

    def test_returns_empty_for_empty_standards(self):
        result = _align_standards_to_grade([], 3)
        assert result == []


class TestOutputFormattingRun:
    """Tests for the run function (Node 4 entry point)."""

    @pytest.mark.asyncio
    async def test_propagates_error_from_previous_node(self):
        state = {
            "topic": "Fracciones",
            "grades": [3, 5],
            "subject": "Matemáticas",
            "available_resources": ["pizarra"],
            "curriculum_standards": [],
            "anchor_activity_adapted": "Actividad",
            "variants_adapted": {"3": "variante"},
            "current_node": "resource_adaptation",
            "error": "resource_adaptation: some error",
        }
        result = await run(state)
        assert result["final_output"] is None
        assert result["current_node"] == "output_formatting"
        assert result["error"] == "resource_adaptation: some error"

    @pytest.mark.asyncio
    async def test_error_when_missing_anchor_activity(self):
        state = {
            "topic": "Fracciones",
            "grades": [3, 5],
            "subject": "Matemáticas",
            "available_resources": ["pizarra"],
            "curriculum_standards": [],
            "anchor_activity_adapted": None,
            "variants_adapted": {"3": "variante"},
            "current_node": "resource_adaptation",
            "error": None,
        }
        result = await run(state)
        assert result["final_output"] is None
        assert "missing anchor_activity_adapted" in result["error"]

    @pytest.mark.asyncio
    async def test_error_when_missing_variants(self):
        state = {
            "topic": "Fracciones",
            "grades": [3, 5],
            "subject": "Matemáticas",
            "available_resources": ["pizarra"],
            "curriculum_standards": [],
            "anchor_activity_adapted": "Actividad ancla",
            "variants_adapted": None,
            "current_node": "resource_adaptation",
            "error": None,
        }
        result = await run(state)
        assert result["final_output"] is None
        assert "missing variants_adapted" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_formatting_with_json_variants(self):
        variant_3 = json.dumps({
            "content": "Contenido grado 3",
            "instructions": "Instrucciones grado 3",
            "exercises": "Ejercicios grado 3",
        })
        variant_5 = json.dumps({
            "content": "Contenido grado 5",
            "instructions": "Instrucciones grado 5",
            "exercises": "Ejercicios grado 5",
        })
        standards = [
            CurriculumStandard(country="CO", grade=3, subject="Matemáticas", text="E3", similarity_score=0.9),
            CurriculumStandard(country="CO", grade=5, subject="Matemáticas", text="E5", similarity_score=0.85),
        ]
        state = {
            "topic": "Fracciones",
            "grades": [3, 5],
            "subject": "Matemáticas",
            "available_resources": ["pizarra", "cuadernos"],
            "curriculum_standards": standards,
            "anchor_activity_adapted": "Actividad ancla sobre fracciones",
            "variants_adapted": {3: variant_3, 5: variant_5},
            "current_node": "resource_adaptation",
            "error": None,
        }
        result = await run(state)

        assert result["current_node"] == "output_formatting"
        assert "error" not in result

        output: ActivityOutput = result["final_output"]
        assert output.topic == "Fracciones"
        assert output.grades == [3, 5]
        assert output.subject_name == "Matemáticas"
        assert output.available_resources == ["pizarra", "cuadernos"]
        assert output.anchor_activity == "Actividad ancla sobre fracciones"
        assert len(output.variants) == 2

        # Variants sorted by grade
        assert output.variants[0].grade == 3
        assert output.variants[0].content == "Contenido grado 3"
        assert output.variants[0].instructions == "Instrucciones grado 3"
        assert output.variants[0].exercises == "Ejercicios grado 3"
        assert len(output.variants[0].aligned_standards) == 1
        assert output.variants[0].aligned_standards[0].text == "E3"

        assert output.variants[1].grade == 5
        assert output.variants[1].content == "Contenido grado 5"
        assert len(output.variants[1].aligned_standards) == 1

    @pytest.mark.asyncio
    async def test_successful_formatting_with_plain_text_variants(self):
        """When variant is not valid JSON, uses fallback."""
        state = {
            "topic": "Ecosistemas",
            "grades": [4],
            "subject": "Ciencias",
            "available_resources": ["pizarra"],
            "curriculum_standards": [],
            "anchor_activity_adapted": "Actividad ancla",
            "variants_adapted": {4: "Texto plano de la variante"},
            "current_node": "resource_adaptation",
            "error": None,
        }
        result = await run(state)

        output: ActivityOutput = result["final_output"]
        assert output.variants[0].grade == 4
        assert output.variants[0].content == "Texto plano de la variante"
        assert len(output.variants[0].instructions) > 0
        assert len(output.variants[0].exercises) > 0

    @pytest.mark.asyncio
    async def test_variants_sorted_by_grade(self):
        """Output variants are always sorted by grade ascending."""
        variant_data = json.dumps({"content": "C", "instructions": "I", "exercises": "E"})
        state = {
            "topic": "Tema",
            "grades": [6, 2, 4],
            "subject": "Arte",
            "available_resources": [],
            "curriculum_standards": [],
            "anchor_activity_adapted": "Ancla",
            "variants_adapted": {6: variant_data, 2: variant_data, 4: variant_data},
            "current_node": "resource_adaptation",
            "error": None,
        }
        result = await run(state)
        output: ActivityOutput = result["final_output"]
        grades_in_output = [v.grade for v in output.variants]
        assert grades_in_output == [2, 4, 6]
