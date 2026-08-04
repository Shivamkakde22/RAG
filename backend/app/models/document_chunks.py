from app.db.postgres import get_cursor

def save_chunks(document_id, chunks):
    query = """
    INSERT INTO document_chunks
    (document_id, chunk_text, chunk_index)
    VALUES
    (%s, %s, %s)
    """

    data = [
        (document_id, chunk, i)
        for i, chunk in enumerate(chunks)
    ]

    with get_cursor() as cursor:
        cursor.executemany(query, data)

def get_chunks_by_document(document_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT chunk_text, chunk_index
            FROM document_chunks
            WHERE document_id=%s
            ORDER BY chunk_index
            """,
            (document_id,)
        )

        return cursor.fetchall()

def get_all_chunks(limit=3000):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT chunk_text, chunk_index, document_id
            FROM document_chunks
            ORDER BY document_id, chunk_index
            LIMIT %s
            """,
            (limit,)
        )
        return cursor.fetchall()


def delete_chunks_by_document(document_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM document_chunks
            WHERE document_id=%s
            """,
            (document_id,)
        )

def search_chunks(query, limit=50):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                dc.id,
                dc.document_id,
                dc.chunk_text,
                dc.chunk_index,
                d.file_name
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.chunk_text ILIKE %s
            ORDER BY d.uploaded_at DESC
            LIMIT %s
            """,
            (f"%{query}%", limit)
        )

        return cursor.fetchall()
