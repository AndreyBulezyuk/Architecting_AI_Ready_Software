"""Deterministic fake embeddings — identical to the demo (swapped for Bedrock on day 2)."""

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
    return "[" + ", ".join(f"{component:.6f}" for component in vector) + "]"
