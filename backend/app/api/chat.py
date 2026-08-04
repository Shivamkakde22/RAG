from flask import Blueprint
from flask import request
from flask import jsonify
from app.services.rag_service import ask_rag
from app.models.chat_history import (
    save_chat,
    get_messages_by_session
)
from app.models.chat_sessions import (
    create_session,
    get_all_sessions,
    delete_all_sessions
)

chat_bp = Blueprint(
    "chat",
    __name__
)

@chat_bp.route(
    "/chat",
    methods=["POST"]
)
def chat():
    try:
        data = request.get_json()
        query = data["query"]
        session_id = data.get("session_id")
        document_id = data.get("document_id")

        if not session_id:
            title = query[:50] + ("..." if len(query) > 50 else "")
            session_id = create_session(title)

        result = ask_rag(
            query,
            document_id
        )

        save_chat(
            session_id,
            query,
            result["answer"]
        )

        result["session_id"] = session_id

        return jsonify(
            result
        )

    except Exception as e:
        print(e)

        return jsonify(
            {
                "error":
                str(e)
            }
        ),500

@chat_bp.route(
    "/sessions",
    methods=["GET"]
)
def sessions():

    return jsonify(
        get_all_sessions()
    )

@chat_bp.route(
    "/sessions",
    methods=["DELETE"]
)
def clear_sessions():

    delete_all_sessions()

    return jsonify(
        {
            "message":
            "All chat history deleted"
        }
    )

@chat_bp.route(
    "/sessions/<int:session_id>/messages",
    methods=["GET"]
)
def session_messages(
    session_id
):

    return jsonify(
        get_messages_by_session(
            session_id
        )
    )
