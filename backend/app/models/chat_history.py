from app.db.postgres import get_cursor

def save_chat(session_id, question, answer):
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_history
            (session_id, question, answer)
            VALUES
            (%s, %s, %s)
            """,
            (session_id, question, answer)
        )

def get_messages_by_session(session_id):
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT question, answer, created_at
            FROM chat_history
            WHERE session_id=%s
            ORDER BY created_at ASC
            """,
            (session_id,)
        )
        return cursor.fetchall()
