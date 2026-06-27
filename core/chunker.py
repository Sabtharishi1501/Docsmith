import tiktoken


def get_encoder():
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str, encoder) -> int:
    if encoder:
        return len(encoder.encode(text))
    return len(text.split())


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list:
    """
    Splits text into overlapping chunks of roughly chunk_size tokens.

    Args:
        text: Full combined scraped text
        chunk_size: Target tokens per chunk
        overlap: Overlapping tokens between chunks

    Returns:
        List of dicts: [{"chunk_id": int, "text": str, "token_count": int}]
    """
    encoder = get_encoder()
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_id = 0

    for para in paragraphs:
        para_tokens = count_tokens(para, encoder)

        if current_tokens + para_tokens > chunk_size and current_chunk:
            chunk_text_str = "\n\n".join(current_chunk)
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text_str,
                "token_count": current_tokens
            })
            chunk_id += 1

            overlap_tokens = 0
            overlap_paras = []
            for p in reversed(current_chunk):
                pt = count_tokens(p, encoder)
                if overlap_tokens + pt <= overlap:
                    overlap_paras.insert(0, p)
                    overlap_tokens += pt
                else:
                    break

            current_chunk = overlap_paras
            current_tokens = overlap_tokens

        current_chunk.append(para)
        current_tokens += para_tokens

    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "text": "\n\n".join(current_chunk),
            "token_count": current_tokens
        })

    print(f"[chunker] Created {len(chunks)} chunks")
    return chunks