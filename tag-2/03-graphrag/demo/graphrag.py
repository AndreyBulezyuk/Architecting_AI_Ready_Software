"""GraphRAG retrieval: vector entry point + graph expansion + cited answer.

The difference to the T2/02 baseline is ONE extra step: from the vector hits we
walk the graph (doc -> shared entities -> related docs) and pull extra context
a pure vector search would never surface for this question.
"""

from dataclasses import dataclass

from config import bedrock_client, settings
from embeddings import embed_query
from kg import INDEX, driver

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
    with driver() as neo4j:
        records = neo4j.execute_query(
            f"CALL db.index.vector.queryNodes('{INDEX}', $k, $query) "
            "YIELD node RETURN node.doc_id AS doc_id, node.seq AS seq, node.text AS text",
            k=k,
            query=embed_query(question),
        ).records
    return [ContextChunk(r["doc_id"], r["seq"], r["text"], "vector") for r in records]


def graph_expansion(hit_doc_ids: set[str], limit: int = 2) -> list[ContextChunk]:
    """Docs that share an entity with a hit doc — plus the entity as provenance."""
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
    return [
        ContextChunk(r["doc_id"], 0, r["text"], f"graph:{','.join(r['shared'])}")
        for r in records
    ]


def answer(question: str, k: int = 3) -> GraphRagAnswer:
    context = vector_hits(question, k)
    context += graph_expansion({chunk.doc_id for chunk in context})

    numbered = "\n\n".join(f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(context))
    response = bedrock_client().converse(
        modelId=settings.chat_model_id,
        system=[{"text": SYSTEM_PROMPT_V1}],
        messages=[{
            "role": "user",
            "content": [{"text": f"Kontext:\n{numbered}\n\nFrage: {question}"}],
        }],
        inferenceConfig={"maxTokens": 400, "temperature": 0},
    )
    message = response["output"].get("message")
    assert message is not None, "model returned no message"
    text = (message.get("content") or [{}])[0].get("text", "")
    return GraphRagAnswer(text=text, context=context)


if __name__ == "__main__":
    result = answer("Wo kann ich wandern und danach im Meer baden?")
    print(result.text)
    print("\nKontext-Herkunft:")
    for chunk in result.context:
        print(f"  {chunk.doc_id}#{chunk.seq} via {chunk.via}")
