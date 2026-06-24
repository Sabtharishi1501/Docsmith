import numpy as np


def retrieve(query: str, index_data: dict, top_k: int = 3) -> list:
    chunks = index_data["chunks"]
    bm25 = index_data["bm25"]
    faiss_index = index_data["faiss_index"]
    vectorizer = index_data["vectorizer"]

    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_max = bm25_scores.max() if bm25_scores.max() > 0 else 1
    bm25_normalized = bm25_scores / bm25_max

    query_vec = vectorizer.transform([query]).toarray().astype("float32")
    norm = np.linalg.norm(query_vec)
    if norm > 0:
        query_vec = query_vec / norm

    distances, indices = faiss_index.search(query_vec, min(top_k * 2, len(chunks)))
    faiss_scores = np.zeros(len(chunks))
    for idx, score in zip(indices[0], distances[0]):
        if idx < len(chunks):
            faiss_scores[idx] = score

    combined_scores = 0.5 * bm25_normalized + 0.5 * faiss_scores
    top_indices = np.argsort(combined_scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        chunk = chunks[idx].copy()
        chunk["score"] = float(combined_scores[idx])
        results.append(chunk)

    return results


def retrieve_context(
    query: str,
    index_data: dict,
    top_k: int = 3,
    max_chars: int = 3000
) -> str:
    """
    Returns retrieved chunks as a single formatted context string.
    max_chars limits total context size to avoid Groq token limit errors.
    """
    results = retrieve(query, index_data, top_k)
    context = "\n\n---\n\n".join(r["text"] for r in results)
    if len(context) > max_chars:
        context = context[:max_chars] + "\n\n[...truncated to fit token limit]"
    return context