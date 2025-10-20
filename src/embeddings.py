# src/embeddings.py
from src.config import openai_client, index, EMBEDDING_MODEL, NAMESPACE
import logging
LOG = logging.getLogger("embeddings")

def get_embedding(text: str) -> list:
    if not text:
        return []
    resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding

def store_embedding(id: str, text: str, metadata: dict):
    if index is None:
        LOG.warning("Pinecone index not initialized; skipping store.")
        return
    emb = get_embedding(text)
    if not emb:
        LOG.warning("Empty embedding for id=%s", id)
        return
    index.upsert(vectors=[{"id": str(id), "values": emb, "metadata": metadata}], namespace=NAMESPACE)
    LOG.info("Upserted vector %s into namespace %s", id, NAMESPACE)
