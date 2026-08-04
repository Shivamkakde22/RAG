import os

from app.services import pdf_parser
from app.services import docx_parser
from app.services.chunker import chunk_text
from app.services.embedding_service import embed_batch
from app.models.document_chunks import save_chunks
from app.models.document import (
    update_processed_chunks,
    mark_document_ready,
    mark_document_failed
)

from app.db.qdrant import (
    make_point_id,
    upsert_points
)

from qdrant_client.models import PointStruct

BATCH_SIZE = 15


def extract_text(file_path):

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".docx":
        return docx_parser.extract_text(file_path)

    return pdf_parser.extract_text(file_path)


def chunk_document(file_path):
    text = extract_text(file_path)
    return chunk_text(text)


def embed_and_upsert_chunks(document_id, chunks, chunk_indices=None, on_progress=None):

    if chunk_indices is None:
        chunk_indices = list(range(len(chunks)))
    else:
        chunk_indices = list(chunk_indices)

    processed = 0

    for start in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[start:start + BATCH_SIZE]
        batch_indices = chunk_indices[start:start + BATCH_SIZE]

        vectors = embed_batch(batch_chunks)

        points = [
            PointStruct(
                id=make_point_id(document_id, chunk_index),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text_value
                }
            )
            for chunk_text_value, chunk_index, vector in zip(batch_chunks, batch_indices, vectors)
        ]

        upsert_points(points)

        processed += len(batch_chunks)
        if on_progress:
            on_progress(processed)


def run_ingestion_in_background(document_id, chunks):
    try:
        embed_and_upsert_chunks(
            document_id,
            chunks,
            on_progress=lambda processed: update_processed_chunks(document_id, processed)
        )
        mark_document_ready(document_id, len(chunks))
    except Exception as e:
        print(f"Ingestion failed for document {document_id}: {e}")
        mark_document_failed(document_id)
