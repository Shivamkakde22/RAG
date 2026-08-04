from app.db.qdrant import create_collection
from app.models.document import get_all_documents
from app.models.document_chunks import get_chunks_by_document
from app.services.ingestion_service import embed_and_upsert_chunks


def backfill():

    create_collection()

    documents = get_all_documents()

    for doc in documents:
        document_id = doc["id"]

        chunks = get_chunks_by_document(document_id)

        if not chunks:
            continue

        texts = [row["chunk_text"] for row in chunks]
        indices = [row["chunk_index"] for row in chunks]

        embed_and_upsert_chunks(document_id, texts, indices)

        print(f"Backfilled document_id={document_id}, {len(chunks)} chunks")


if __name__ == "__main__":
    backfill()
