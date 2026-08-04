from app.db.postgres import get_cursor


def cleanup_duplicate_documents():

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT id FROM documents
            WHERE id NOT IN (
                SELECT MAX(id) FROM documents GROUP BY file_name
            )
            """
        )

        stale_ids = [row["id"] for row in cursor.fetchall()]

        if not stale_ids:
            print("No duplicate documents found")
            return

        cursor.execute(
            "DELETE FROM chat_history WHERE document_id = ANY(%s)",
            (stale_ids,)
        )

        cursor.execute(
            "DELETE FROM document_chunks WHERE document_id = ANY(%s)",
            (stale_ids,)
        )

        cursor.execute(
            "DELETE FROM documents WHERE id = ANY(%s)",
            (stale_ids,)
        )

        print(f"Deleted {len(stale_ids)} duplicate document rows: {stale_ids}")


if __name__ == "__main__":
    cleanup_duplicate_documents()
