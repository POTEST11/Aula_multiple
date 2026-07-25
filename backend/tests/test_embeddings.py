"""Unit tests for the EmbeddingService (local sentence-transformers)."""

import pytest

from app.rag.embeddings import EmbeddingService

EMBEDDING_DIM = 384


@pytest.fixture(scope="module")
def embedding_service():
    """Create a shared EmbeddingService instance (model loads once)."""
    return EmbeddingService()


class TestEmbeddingServiceGenerate:
    """Tests for EmbeddingService.generate()."""

    @pytest.mark.asyncio
    async def test_generate_returns_384_floats(self, embedding_service):
        result = await embedding_service.generate("Hola mundo")
        assert isinstance(result, list)
        assert len(result) == EMBEDDING_DIM
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_generate_normalized_vector(self, embedding_service):
        """Normalized embeddings should have L2 norm close to 1.0."""
        import math

        result = await embedding_service.generate("Vector normalizado")
        norm = math.sqrt(sum(x * x for x in result))
        assert abs(norm - 1.0) < 1e-5

    @pytest.mark.asyncio
    async def test_generate_empty_text_raises_value_error(self, embedding_service):
        with pytest.raises(ValueError, match="no puede estar vacío"):
            await embedding_service.generate("")

    @pytest.mark.asyncio
    async def test_generate_whitespace_only_raises_value_error(self, embedding_service):
        with pytest.raises(ValueError, match="no puede estar vacío"):
            await embedding_service.generate("   ")

    @pytest.mark.asyncio
    async def test_generate_different_texts_produce_different_embeddings(
        self, embedding_service
    ):
        emb1 = await embedding_service.generate("Matemáticas de tercer grado")
        emb2 = await embedding_service.generate("Historia del arte contemporáneo")
        assert emb1 != emb2


class TestEmbeddingServiceGenerateBatch:
    """Tests for EmbeddingService.generate_batch()."""

    @pytest.mark.asyncio
    async def test_generate_batch_returns_correct_count(self, embedding_service):
        texts = ["Texto uno", "Texto dos", "Texto tres"]
        results = await embedding_service.generate_batch(texts)
        assert len(results) == 3
        assert all(len(emb) == EMBEDDING_DIM for emb in results)

    @pytest.mark.asyncio
    async def test_generate_batch_each_embedding_is_normalized(self, embedding_service):
        import math

        texts = ["Primer texto", "Segundo texto"]
        results = await embedding_service.generate_batch(texts)
        for emb in results:
            norm = math.sqrt(sum(x * x for x in emb))
            assert abs(norm - 1.0) < 1e-5

    @pytest.mark.asyncio
    async def test_generate_batch_empty_list_raises_value_error(self, embedding_service):
        with pytest.raises(ValueError, match="no puede estar vacía"):
            await embedding_service.generate_batch([])

    @pytest.mark.asyncio
    async def test_generate_batch_with_empty_text_raises_value_error(
        self, embedding_service
    ):
        with pytest.raises(ValueError, match="posición 1"):
            await embedding_service.generate_batch(["válido", ""])

    @pytest.mark.asyncio
    async def test_generate_batch_consistent_with_single(self, embedding_service):
        """Batch results should match individual generate calls."""
        text = "Consistencia entre batch y single"
        single = await embedding_service.generate(text)
        batch = await embedding_service.generate_batch([text])
        # Float precision: allow tiny difference
        for s, b in zip(single, batch[0]):
            assert abs(s - b) < 1e-6
