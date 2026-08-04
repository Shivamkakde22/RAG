from app.db.postgres import get_cursor

def create_session(title):
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_sessions (title)
            VALUES (%s)
            RETURNING id
            """,
            (title,)
        )

        return cursor.fetchone()["id"]

def get_all_sessions():
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, created_at
            FROM chat_sessions
            ORDER BY created_at DESC
            """
        )

        return cursor.fetchall()

def delete_all_sessions():
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM chat_history")
        cursor.execute("DELETE FROM chat_sessions")
