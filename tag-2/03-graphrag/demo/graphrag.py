"""GraphRAG retrieval: vector entry point + graph expansion + cited answer.

The difference to the T2/02 baseline is ONE extra step: from the vector hits we
walk the graph (doc -> shared entities -> related docs) and pull extra context
a pure vector search would never surface for this question.

Traced via OTel → Langfuse: each step (vector_hits, graph_expansion, LLM call)
appears as a child span in the trace tree — visible in the Langfuse UI.
Neo4j node/relationship data is attached as structured metadata on each span.
"""

import json
from dataclasses import dataclass, asdict

from config import bedrock_client, settings
from embeddings import embed_query
from kg import INDEX, driver
from tracing import tracer

SYSTEM_PROMPT_V1 = """Du bist Reise-Assistent von TravelMate.
Antworte ausschließlich auf Basis des nummerierten Kontexts, auf Deutsch, knapp.
Zitiere die verwendeten Kontext-Nummern im Text als [n].
Wenn der Kontext die Frage nicht beantwortet, antworte exakt mit: KEINE_ANTWORT_IM_KONTEXT"""


@dataclass
class ContextChunk:
    doc_id: str
    seq: int
    text: str
    via: str  # "vector" or "graph:<entity>" — provenance for the audit trail


@dataclass
class GraphRagAnswer:
    text: str
    context: list[ContextChunk]

    @property
    def doc_ids(self) -> set[str]:
        return {chunk.doc_id for chunk in self.context}


def vector_hits(question: str, k: int = 3) -> list[ContextChunk]:
    with tracer.start_as_current_span("vector_search") as span:
        span.set_attribute("langfuse.observation.type", "retriever")
        span.set_attribute("langfuse.observation.input", question)
        with driver() as neo4j:
            records = neo4j.execute_query(
                f"CALL db.index.vector.queryNodes('{INDEX}', $k, $query) "
                "YIELD node, score "
                "RETURN node.doc_id AS doc_id, node.seq AS seq, node.text AS text, "
                "score AS score, labels(node) AS labels",
                k=k,
                query=embed_query(question),
            ).records
        hits = [ContextChunk(r["doc_id"], r["seq"], r["text"], "vector") for r in records]

        # structured node data for Langfuse — shows exactly what came back from Neo4j
        nodes = [
            {
                "doc_id": r["doc_id"],
                "seq": r["seq"],
                "score": round(float(r["score"]), 4),
                "labels": r["labels"],
                "text_preview": (r["text"] or "")[:120],
            }
            for r in records
        ]
        span.set_attribute("langfuse.observation.output", json.dumps(nodes, ensure_ascii=False))
        return hits


def graph_expansion(hit_doc_ids: set[str], limit: int = 2) -> list[ContextChunk]:
    """Docs that share an entity with a hit doc — plus the entity as provenance."""
    with tracer.start_as_current_span("graph_expansion") as span:
        span.set_attribute("langfuse.observation.type", "retriever")
        span.set_attribute("langfuse.observation.input", json.dumps(sorted(hit_doc_ids)))

        # Step 1: find the traversed paths (doc → entity → doc)
        with driver() as neo4j:
            path_records = neo4j.execute_query(
                """
                MATCH (hit:T3Doc)-[r1:MENTIONS]->(e:T3Entity)<-[r2:MENTIONS]-(related:T3Doc)
                WHERE hit.doc_id IN $doc_ids AND NOT related.doc_id IN $doc_ids
                RETURN hit.doc_id AS from_doc, e.name AS entity_name, e.type AS entity_type,
                       related.doc_id AS to_doc
                ORDER BY e.name
                """,
                doc_ids=list(hit_doc_ids),
            ).records

        # Step 2: get the expanded docs with their leading chunks
        with driver() as neo4j:
            records = neo4j.execute_query(
                """
                MATCH (hit:T3Doc)-[:MENTIONS]->(e:T3Entity)<-[:MENTIONS]-(related:T3Doc)
                WHERE hit.doc_id IN $doc_ids AND NOT related.doc_id IN $doc_ids
                WITH related, collect(DISTINCT e.name) AS shared, count(DISTINCT e) AS overlap
                ORDER BY overlap DESC LIMIT $limit
                MATCH (related)<-[:PART_OF]-(c:T3Chunk {seq: 0})
                RETURN related.doc_id AS doc_id, c.text AS text, shared
                """,
                doc_ids=list(hit_doc_ids),
                limit=limit,
            ).records

        hits = [
            ContextChunk(r["doc_id"], 0, r["text"], f"graph:{','.join(r['shared'])}")
            for r in records
        ]

        # structured relationship data: shows the graph traversal in Langfuse
        traversal = [
            {
                "from": dict(r)["from_doc"],
                "entity": dict(r)["entity_name"],
                "entity_type": dict(r)["entity_type"],
                "to": dict(r)["to_doc"],
            }
            for r in path_records
        ]
        span.set_attribute(
            "langfuse.observation.output",
            json.dumps(
                {"paths": traversal, "expanded_docs": [h.doc_id for h in hits]}, ensure_ascii=False
            ),
        )
        return hits


def answer(question: str, k: int = 3, *, tags: list[str] | None = None) -> GraphRagAnswer:
    with tracer.start_as_current_span("graphrag.answer") as span:
        span.set_attribute("langfuse.trace.tags", tags or ["tag-2/03", "graphrag"])
        span.set_attribute("gen_ai.prompt", question)

        context = vector_hits(question, k)
        context += graph_expansion({chunk.doc_id for chunk in context})

        # summary metadata on the root span: full graph context at a glance
        graph_summary = {
            "vector_hits": [c.doc_id for c in context if c.via == "vector"],
            "graph_expansions": [
                {"doc_id": c.doc_id, "via": c.via} for c in context if c.via.startswith("graph:")
            ],
            "total_context_chunks": len(context),
            "unique_docs": sorted({c.doc_id for c in context}),
        }
        span.set_attribute("langfuse.trace.metadata.graph_context", json.dumps(graph_summary))

        numbered = "\n\n".join(f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(context))
        response = bedrock_client().converse(
            modelId=settings.chat_model_id,
            system=[{"text": SYSTEM_PROMPT_V1}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": f"Kontext:\n{numbered}\n\nFrage: {question}"}],
                }
            ],
            inferenceConfig={"maxTokens": 400, "temperature": 0},
        )
        message = response["output"].get("message")
        assert message is not None, "model returned no message"
        usage = response["usage"]
        text = (message.get("content") or [{}])[0].get("text", "")

        span.set_attribute("gen_ai.system", "aws.bedrock")
        span.set_attribute("gen_ai.request.model", settings.chat_model_id)
        span.set_attribute("gen_ai.usage.input_tokens", usage["inputTokens"])
        span.set_attribute("gen_ai.usage.output_tokens", usage["outputTokens"])
        span.set_attribute("gen_ai.completion", text)

        return GraphRagAnswer(text=text, context=context)


if __name__ == "__main__":
    result = answer("Wo kann ich wandern und danach im Meer baden?")
    print(result.text)
    print("\nKontext-Herkunft:")
    for chunk in result.context:
        print(f"  {chunk.doc_id}#{chunk.seq} via {chunk.via}")
