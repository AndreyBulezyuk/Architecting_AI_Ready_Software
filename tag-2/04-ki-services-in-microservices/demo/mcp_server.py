"""MCP server wrapping the same RAG backbone as the REST service.

Demonstrates the duality: one `rag.py`, two interfaces — FastAPI for
HTTP consumers, MCP for agents and IDEs. No Docker, no extra infra;
runs as a stdio subprocess that any MCP client can spawn.

Run standalone:  uv run python mcp_server.py
Connect from Claude Desktop, Cursor, or a Strands agent (tag-2/05).
"""

from fastmcp import FastMCP

import rag
import store

mcp = FastMCP("travelmate-rag")


@mcp.tool
def search_travel_reports(query: str, k: int = 3) -> str:
    """Semantic search through TravelMate travel reports.

    Returns the top-k matching text chunks with document IDs and similarity
    scores. Use this to find relevant content before asking a question.
    """
    hits = store.search(query, k=k)
    if not hits:
        return "No matching reports found."
    lines = []
    for i, hit in enumerate(hits, 1):
        lines.append(f"[{i}] ({hit.doc_id}, seq={hit.seq}, score={hit.score:.3f}) {hit.text}")
    return "\n\n".join(lines)


@mcp.tool
def ask_travelmate(question: str) -> str:
    """Ask a question about TravelMate travel reports.

    Uses RAG: retrieves relevant context from the vector store, then
    generates an answer grounded in those results. Returns the answer
    text with source references [n].
    """
    result = rag.answer(question)
    refused = rag.REFUSAL_MARKER in result.text
    sources = ", ".join(f"{h.doc_id}[{h.seq}]" for h in result.sources)
    header = f"sources=[{sources}] model={result.model_id} tokens={result.input_tokens}/{result.output_tokens}"
    if refused:
        return f"{header}\n\n(Keine passende Antwort im Kontext.)"
    return f"{header}\n\n{result.text}"


if __name__ == "__main__":
    mcp.run()
