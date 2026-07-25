"""Local embedding service using sentence-transformers (all-MiniLM-L6-v2)."""

import asyncio

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Genera embeddings localmente usando sentence-transformers (all-MiniLM-L6-v2,
    384 dimensiones). Corre en CPU, sin llamadas de red ni API key externa.
    El modelo se carga una sola vez al iniciar el proceso.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    async def generate(self, text: str) -> list[float]:
        """
        Genera embedding vectorial (384d) para un texto dado, localmente.

        Usa asyncio.to_thread para no bloquear el event loop ya que
        model.encode() es una operación síncrona de CPU.

        Args:
            text: Texto de entrada para generar el embedding.

        Returns:
            Lista de floats con 384 dimensiones representando el embedding.

        Raises:
            ValueError: Si el texto está vacío.
        """
        if not text or not text.strip():
            raise ValueError("El texto no puede estar vacío")

        embedding = await asyncio.to_thread(
            self.model.encode, text, normalize_embeddings=True
        )
        return embedding.tolist()

    async def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Genera embeddings en batch para múltiples textos, localmente.

        Procesa todos los textos en una sola llamada a model.encode() para
        aprovechar la paralelización interna de sentence-transformers.

        Args:
            texts: Lista de textos de entrada.

        Returns:
            Lista de embeddings (cada uno una lista de 384 floats).

        Raises:
            ValueError: Si la lista está vacía o contiene textos vacíos.
        """
        if not texts:
            raise ValueError("La lista de textos no puede estar vacía")

        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(
                    f"El texto en posición {i} no puede estar vacío"
                )

        embeddings = await asyncio.to_thread(
            self.model.encode, texts, normalize_embeddings=True
        )
        return embeddings.tolist()
