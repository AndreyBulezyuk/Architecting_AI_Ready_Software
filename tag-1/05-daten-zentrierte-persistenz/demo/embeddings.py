"""Deterministic fake embeddings (see theorie.md, slide 6).

Same pipeline shape as real embeddings, zero API cost, fully testable:
words are hashed into a fixed number of buckets, the vector is L2-normalized
so cosine similarity behaves sensibly. On day 2 this single function is
replaced by a Bedrock embeddings call — nothing else changes.
"""

import hashlib
import math
import re

from config import settings


def embed(text: str) -> list[float]:
    vector = [0.0] * settings.embedding_dimensions
    for word in re.findall(r"\w+", text.lower()):
        digest = hashlib.sha256(word.encode()).digest()
        bucket = digest[0] % settings.embedding_dimensions
        vector[bucket] += 1.0
    norm = math.sqrt(sum(component * component for component in vector)) or 1.0
    return [component / norm for component in vector]


def to_pgvector(vector: list[float]) -> str:
    """pgvector literal format: '[0.1, 0.2, ...]'."""
    return "[" + ", ".join(f"{component:.6f}" for component in vector) + "]"
