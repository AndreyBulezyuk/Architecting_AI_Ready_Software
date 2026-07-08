"""The AI capability as a regular microservice: versioned contract, honest errors.

Run: uv run fastapi dev service.py
"""

import uuid
from typing import Literal

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import rag
from store import driver

app = FastAPI(title="TravelMate Assistant Service")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class SourceRef(BaseModel):
    doc_id: str
    seq: int


class AskResponse(BaseModel):
    schema_version: Literal["1"] = "1"
    request_id: str
    answer: str
    refused: bool
    sources: list[SourceRef]
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


@app.post("/v1/ask")
def ask(request: AskRequest) -> AskResponse:
    request_id = str(uuid.uuid4())
    try:
        result = rag.answer(request.question)
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "")
        if code == "ThrottlingException":
            # honest backpressure beats a fake answer — the caller decides what to do
            # (headers must live on the HTTPException — FastAPI builds a fresh response for it)
            raise HTTPException(
                status_code=503,
                detail="model is throttling, retry later",
                headers={"Retry-After": "2"},
            )
        raise HTTPException(status_code=502, detail=f"upstream model error: {code}")
    # one log line per call: the raw material for day-3 observability & FinOps
    print(
        f"request_id={request_id} model={result.model_id} "
        f"tokens={result.input_tokens}/{result.output_tokens} latency_ms={result.latency_ms}"
    )
    return AskResponse(
        request_id=request_id,
        answer=result.text,
        refused=rag.REFUSAL_MARKER in result.text,
        sources=[SourceRef(doc_id=hit.doc_id, seq=hit.seq) for hit in result.sources],
        model_id=result.model_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    # cheap by design: check our OWN dependencies, never call the paid model
    try:
        with driver() as neo4j:
            neo4j.verify_connectivity()  # pyright: ignore[reportUnknownMemberType]
    except Exception:
        raise HTTPException(status_code=503, detail="neo4j unreachable")
    return {"status": "ok"}
