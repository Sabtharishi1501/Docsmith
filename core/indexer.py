import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer


def get_embeddings(texts: list):
    vectorizer = TfidfVectorizer(
        max_features=768,
        analyzer="word",
        ngram_range=(1, 2)
    )
    matrix = vectorizer.fit_transform(texts).toarray().astype("float32")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix = matrix / norms
    return matrix, vectorizer


def build_index(chunks: list) -> dict:
    """
    Builds FAISS vector index + BM25 keyword index from chunks.

    Args:
        chunks: List of chunk dicts from chunker.py

    Returns:
        {
            "faiss_index": faiss.Index,
            "bm25": BM25Okapi,
            "vectorizer": TfidfVectorizer,
            "chunks": list
        }
    """
    texts = [c["text"] for c in chunks]

    print("[indexer] Building BM25 index...")
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)

    print("[indexer] Building FAISS index...")
    embeddings, vectorizer = get_embeddings(texts)
    dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatIP(dimension)
    faiss_index.add(embeddings)

    print(f"[indexer] Index built — {len(chunks)} chunks indexed")

    return {
        "faiss_index": faiss_index,
        "bm25": bm25,
        "vectorizer": vectorizer,
        "chunks": chunks
    }