from app.infra.session import get_session
from app.services.rag.ingestion import ingest_knowledge_base


def main() -> None:
    with get_session() as session:
        summary = ingest_knowledge_base(session)

    print(
        "KB ingestion complete:",
        f"total={summary.total}",
        f"inserted={summary.inserted}",
        f"updated={summary.updated}",
        f"deleted={summary.deleted}",
        f"skipped={summary.skipped}",
    )


if __name__ == "__main__":
    main()
