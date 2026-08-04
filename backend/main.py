import atexit
import os

from flask import Flask
from flask import jsonify
from flask_cors import CORS
from app.api.documents import document_bp
from app.api.chat import chat_bp
from app.api.evaluate import evaluate_bp
from app.api.system import system_bp
from app.db.qdrant import create_collection
from app.db.postgres import ensure_chat_schema
from app.mcp.hub import mcp_hub

app = Flask(__name__)
# Maximum upload size = 100 MB
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
CORS(app, origins=ALLOWED_ORIGINS)

create_collection()
ensure_chat_schema()

mcp_hub.start()
atexit.register(mcp_hub.stop)

app.register_blueprint(
    document_bp
)
app.register_blueprint(
    chat_bp
)
app.register_blueprint(
    evaluate_bp
)
app.register_blueprint(
    system_bp
)
@app.route("/")
def home():
    return {
        "message":
        "RAG API Running"
    }

@app.errorhandler(413)
def too_large(e):
    return jsonify(
        {
            "error":
            "File size exceeds 100 MB"
        }
    ), 413

if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        port=int(os.getenv("BACKEND_PORT", "5050")),
        threaded=True
    )