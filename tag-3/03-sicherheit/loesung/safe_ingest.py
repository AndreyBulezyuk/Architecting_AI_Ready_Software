"""Screen documents with apply_guardrail BEFORE they enter the knowledge base.

This is the defence against INDIRECT prompt injection (OWASP LLM01/LLM08): a
poisoned document carries the attack payload, and a converse-time guardrail would
only see it after retrieval has already put it into the prompt. Screening at
ingest keeps the payload out of the store entirely.
"""

from dataclasses import dataclass

import store
from scan import scan


@dataclass
class IngestReport:
    ingested: list[str]
    rejected: list[str]


def safe_ingest(documents: dict[str, str], guardrail_id: str) -> IngestReport:
    """Ingest only documents that pass the guardrail; reject (and report) the rest."""
    report = IngestReport(ingested=[], rejected=[])
    for doc_id, text in documents.items():
        # INPUT source: we treat the document as untrusted input to our system
        result = scan(text, guardrail_id, source="INPUT")
        if result.intervened:
            report.rejected.append(doc_id)
            continue
        store.ingest_document(doc_id, text)
        report.ingested.append(doc_id)
    return report
