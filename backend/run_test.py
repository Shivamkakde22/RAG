from flask import Flask

from flask_cors import CORS

from app.api.documents import document_bp

from app.api.chat import chat_bp


app = Flask(__name__)

CORS(app)


app.register_blueprint(document_bp)

app.register_blueprint(chat_bp)


@app.route("/")

def home():

    return {

        "message":"RAG API Running"

    }


if __name__ == "__main__":

    app.run(

        debug=True

    )