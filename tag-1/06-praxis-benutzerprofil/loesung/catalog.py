"""Offer catalog in Neo4j: seed + vector recommendations (chapter 05 patterns)."""

from typing import LiteralString, cast

from neo4j import Driver, GraphDatabase

from config import settings
from embeddings import embed

OFFERS: list[tuple[str, str]] = [
    ("algarve-familie", "flacher strand kinder familie baden sandburg meer"),
    ("nordsee-watt", "watt strand familie kinder meer ebbe flut"),
    ("kreta-resort", "strand resort pool meer sonne baden komfort"),
    ("stubai-huette", "berge wandern huette gipfel anstrengung panorama"),
    ("dolomiten-klettern", "klettern berge seil huette alpin anstrengung"),
    ("allgaeu-wandern", "wandern wiesen berge familie leicht panorama"),
    ("tokio-city", "stadt kultur essen technik tempel u-bahn"),
    ("rom-antike", "stadt kultur geschichte museum essen antike"),
    ("paris-kunst", "stadt kunst museum kultur essen mode"),
    ("lappland-aurora", "schnee winter polarlicht hund schlitten kalt"),
    ("island-geysir", "vulkan geysir natur bad heiss quelle"),
    ("azoren-wale", "wale boot natur meer insel wandern"),
    ("toskana-wein", "wein essen landschaft genuss komfort huegel"),
    ("provence-lavendel", "lavendel genuss landschaft markt essen sonne"),
    ("ligurien-kueste", "kueste wandern meer doerfer essen baden"),
    ("kopenhagen-rad", "stadt fahrrad design essen hafen familie"),
    ("schwarzwald-familie", "wald familie kinder wandern see baden"),
    ("garda-sport", "see surfen rad klettern sport baden"),
    ("marokko-wueste", "wueste kamel zelt sterne abenteuer markt"),
    ("norwegen-fjord", "fjord boot wandern natur wasserfall panorama"),
]


def driver() -> Driver:
    return GraphDatabase.driver(  # pyright: ignore[reportUnknownMemberType]
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def seed_catalog() -> int:
    with driver() as neo4j:
        ddl = (
            f"CREATE VECTOR INDEX {settings.offer_index_name} IF NOT EXISTS "
            "FOR (o:UebOffer) ON (o.embedding) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {settings.embedding_dimensions}, "
            "`vector.similarity_function`: 'cosine'}}"
        )
        neo4j.execute_query(cast(LiteralString, ddl))
        neo4j.execute_query("MATCH (o:UebOffer) DETACH DELETE o")
        neo4j.execute_query(
            "UNWIND $rows AS row "
            "CREATE (:UebOffer {offer_id: row.offer_id, description: row.description, "
            "embedding: row.embedding})",
            rows=[
                {"offer_id": offer_id, "description": text, "embedding": embed(text)}
                for offer_id, text in OFFERS
            ],
        )
        neo4j.execute_query("CALL db.awaitIndexes(60)")
    return len(OFFERS)


def recommend(interests: list[str], k: int | None = None) -> list[str]:
    """Top-k offer ids for an interest list (same embedding function as the catalog!)."""
    if not interests:
        return []
    with driver() as neo4j:
        query_text = (
            f"CALL db.index.vector.queryNodes('{settings.offer_index_name}', $k, $query) "
            "YIELD node RETURN node.offer_id AS offer_id"
        )
        records = neo4j.execute_query(
            cast(LiteralString, query_text),
            k=k or settings.recommendation_count,
            query=embed(" ".join(interests)),
        ).records
    return [record["offer_id"] for record in records]


if __name__ == "__main__":
    print(f"seeded {seed_catalog()} offers")
