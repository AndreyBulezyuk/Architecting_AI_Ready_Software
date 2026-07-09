"""Fixed-size chunking with overlap, cutting at paragraph boundaries where possible.

Pure function, no AWS — unit-testable offline (theorie.md, slide 3).
"""


def chunk_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if overlap_chars >= max_chars:
        raise ValueError("overlap must be smaller than the chunk size")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            # overlap: carry the tail of the previous chunk into the next one
            current = current[-overlap_chars:] + "\n\n" + paragraph if overlap_chars else paragraph
        else:
            current = paragraph
        # a single paragraph longer than max_chars gets hard-split
        while len(current) > max_chars:
            chunks.append(current[:max_chars])
            current = current[max_chars - overlap_chars:] if overlap_chars else current[max_chars:]
    if current:
        chunks.append(current)
    return chunks
