"""Knowledge-graph construction: chunks + LLM-extracted entities.

Graph model (deliberately small — the ontology IS the hard part, theorie.md slide 3):
    (:EvalDoc {doc_id})<-[:PART_OF]-(:EvalChunk {seq, text, embedding})
    (:EvalDoc)-[:MENTIONS]->(:EvalEntity {name, type})

Entity extraction uses the forced-tool-call contract from T2/01 — no JSON-from-text
parsing, hence no code-fence trap.
"""

from typing import Any, Literal, LiteralString, cast

from neo4j import Driver, GraphDatabase
from pydantic import BaseModel, Field, ValidationError

from chunking import chunk_text
from config import bedrock_client, settings
from embeddings import embed_documents

INDEX = "eval_chunk_embeddings"
TOOL_NAME = "record_entities"


class Entity(BaseModel):
    name: str = Field(description="lowercase german base form, e.g. 'wandern'")
    type: Literal["destination", "activity", "audience"]


class ExtractedEntities(BaseModel):
    entities: list[Entity] = Field(max_length=8)


def driver() -> Driver:
    return GraphDatabase.driver(  # pyright: ignore[reportUnknownMemberType]
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def init_schema() -> None:
    with driver() as neo4j:
        ddl = (
            f"CREATE VECTOR INDEX {INDEX} IF NOT EXISTS "
            "FOR (c:EvalChunk) ON (c.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {settings.embedding_dimensions}, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        neo4j.execute_query(cast(LiteralString, ddl))
        neo4j.execute_query("CALL db.awaitIndexes(60)")


def _tool_call_input(text: str, hint: str | None) -> dict[str, Any]:
    prompt = (
        "Extrahiere die wichtigsten Entitäten aus diesem Reisebericht. "
        "Typen: destination (Orte/Regionen), activity (Aktivitäten wie 'wandern', "
        "'baden'), audience (Zielgruppen wie 'familie', 'paare'). "
        "Namen: deutsche Grundform, Kleinbuchstaben, ein Wort wo möglich.\n\n"
        f"Text:\n{text}"
    )
    if hint:
        prompt += f"\n\nHinweis, dein letzter Versuch war ungültig: {hint}"
    response = bedrock_client().converse(
        modelId=settings.chat_model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        toolConfig={
            "tools": [{
                "toolSpec": {
                    "name": TOOL_NAME,
                    "description": "Records the extracted entities",
                    "inputSchema": {"json": ExtractedEntities.model_json_schema()},
                }
            }],
            "toolChoice": {"tool": {"name": TOOL_NAME}},
        },
        inferenceConfig={"maxTokens": 600, "temperature": 0},
    )
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    for block in message.get("content") or []:
        tool_use = block.get("toolUse")
        if tool_use and tool_use.get("name") == TOOL_NAME:
            return dict(tool_use.get("input") or {})
    raise RuntimeError("model did not call the required tool")


def extract_entities(text: str) -> ExtractedEntities:
    hint: str | None = None
    for _ in range(2):
        raw = _tool_call_input(text, hint)
        try:
            return ExtractedEntities.model_validate(raw)
        except ValidationError as error:
            hint = str(error)
    raise ValueError(f"model output failed validation twice: {hint}")


def ingest_document(doc_id: str, text: str) -> tuple[int, int]:
    """Chunks + embeddings + entities into the graph; returns (chunks, entities)."""
    chunks = chunk_text(text, settings.chunk_max_chars, settings.chunk_overlap_chars)
    vectors = embed_documents(chunks)
    extraction = extract_entities(text)
    with driver() as neo4j:
        neo4j.execute_query(
            "MATCH (d:EvalDoc {doc_id: $doc_id}) OPTIONAL MATCH (d)<-[:PART_OF]-(c:EvalChunk) "
            "DETACH DELETE d, c",
            doc_id=doc_id,
        )
        neo4j.execute_query(
            "MERGE (d:EvalDoc {doc_id: $doc_id}) "
            "WITH d UNWIND $rows AS row "
            "CREATE (c:EvalChunk {doc_id: $doc_id, seq: row.seq, text: row.text, "
            "embedding: row.embedding})-[:PART_OF]->(d)",
            doc_id=doc_id,
            rows=[
                {"seq": seq, "text": chunk, "embedding": vector}
                for seq, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
            ],
        )
        # entities are shared across documents — MERGE deduplicates by name+type
        neo4j.execute_query(
            "MATCH (d:EvalDoc {doc_id: $doc_id}) "
            "UNWIND $entities AS entity "
            "MERGE (e:EvalEntity {name: entity.name, type: entity.type}) "
            "MERGE (d)-[:MENTIONS]->(e)",
            doc_id=doc_id,
            entities=[entity.model_dump() for entity in extraction.entities],
        )
        neo4j.execute_query("CALL db.awaitIndexes(60)")
    return len(chunks), len(extraction.entities)
