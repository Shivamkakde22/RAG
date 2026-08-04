from app.db.postgres import get_cursor

def create_collection_record(name):
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO collections (name)
            VALUES (%s)
            RETURNING id
            """,
            (name,)
        )

        return cursor.fetchone()["id"]

def get_all_collections():
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, created_at
            FROM collections
            ORDER BY created_at DESC
            """
        )

        return cursor.fetchall()
