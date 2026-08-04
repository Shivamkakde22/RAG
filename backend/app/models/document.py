from app.db.postgres import get_cursor

def save_document(file_name, file_path, file_size, total_chunks, collection_id=None):
    query = """
    INSERT INTO documents
    (file_name, file_path, file_size, total_chunks, status, collection_id)
    VALUES
    (%s, %s, %s, %s, 'pending', %s)
    RETURNING id;
    """

    with get_cursor() as cursor:
        cursor.execute(
            query,
            (
                file_name,
                file_path,
                file_size,
                total_chunks,
                collection_id
            )
        )

        return cursor.fetchone()["id"]

def set_total_chunks(document_id, total_chunks):
    with get_cursor() as cursor:
        cursor.execute(
            """
            UPDATE documents
            SET total_chunks=%s
            WHERE id=%s
            """,
            (total_chunks, document_id)
        )

def update_processed_chunks(document_id, processed_chunks):
    with get_cursor() as cursor:
        cursor.execute(
            """
            UPDATE documents
            SET processed_chunks=%s
            WHERE id=%s
            """,
            (processed_chunks, document_id)
        )

def mark_document_ready(document_id, total_chunks):
    with get_cursor() as cursor:
        cursor.execute(
            """
            UPDATE documents
            SET total_chunks=%s, status='ready'
            WHERE id=%s
            """,
            (total_chunks, document_id)
        )

def mark_document_failed(document_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            UPDATE documents
            SET status='failed'
            WHERE id=%s
            """,
            (document_id,)
        )

def get_all_documents():
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM documents
            ORDER BY uploaded_at DESC
            """
        )

        return cursor.fetchall()

def get_document_by_id(document_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM documents
            WHERE id=%s
            """,
            (document_id,)
        )

        return cursor.fetchone()

def delete_document(document_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM documents
            WHERE id=%s
            """,
            (document_id,)
        )
