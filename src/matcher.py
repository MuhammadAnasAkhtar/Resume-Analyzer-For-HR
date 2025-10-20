# src/matcher.py
from src.embeddings import get_embedding
from src.config import index, NAMESPACE
import logging

LOG = logging.getLogger("matcher")

def find_best_match(query_text: str, top_k: int = 3):
    if index is None:
        LOG.warning("Pinecone not configured; returning empty matches.")
        return {"matches": []}
    query_vector = get_embedding(query_text)
    if not query_vector:
        return {"matches": []}
    res = index.query(vector=query_vector, top_k=top_k, include_metadata=True, namespace=NAMESPACE)
    matches = []
    for m in res.get("matches", []) or []:
        matches.append({"id": m.get("id"), "score": m.get("score") or m.get("distance"), "metadata": m.get("metadata")})
    return {"matches": matches}
