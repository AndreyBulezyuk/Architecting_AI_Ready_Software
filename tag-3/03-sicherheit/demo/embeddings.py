"""Real embeddings via Bedrock (Cohere Embed Multilingual v3).

This module replaces the fake hash embeddings from tag-1/05 — same signatures,
same store, real semantics. Note the input_type split (theorie.md, slide 4).
"""

import json
from typing import Literal

from config import bedrock_runtime_client, settings

COHERE_MAX_BATCH = 96

InputType = Literal["search_document", "search_query"]


def _embed(texts: list[str], input_type: InputType) -> list[list[float]]:
    client = bedrock_runtime_client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), COHERE_MAX_BATCH):
        body = json.dumps(
            {"texts": texts[start : start + COHERE_MAX_BATCH], "input_type": input_type}
        )
        response = client.invoke_model(modelId=settings.embedding_model_id, body=body)
        payload = json.loads(response["body"].read())
        vectors.extend(payload["embeddings"])
    return vectors


def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "search_document")


def embed_query(text: str) -> list[float]:
    return _embed([text], "search_query")[0]
