from flask import Blueprint
from flask import request
from flask import jsonify

import os
import threading
import uuid
from werkzeug.utils import secure_filename

from app.services.ingestion_service import (
    chunk_document,
    run_ingestion_in_background
)

from app.models.document import (
    save_document,
    set_total_chunks,
    mark_document_failed,
    get_all_documents,
    get_document_by_id,
    delete_document
)

from app.models.document_chunks import (
    save_chunks,
    delete_chunks_by_document,
    search_chunks
)

from app.db.qdrant import delete_points_by_document

from app.models.collections import (
    create_collection_record,
    get_all_collections
)


document_bp = Blueprint(

    "documents",

    __name__

)

ALLOWED_EXTENSIONS = (".pdf", ".docx")


@document_bp.route(

    "/upload",

    methods=["GET","POST"]

)
def upload_document():


    if "file" not in request.files:


        return jsonify(

            {

                "error":

                "No file uploaded"

            }

        ),400



    file = request.files["file"]
    
    if request.method=="GET":
        return jsonify(

        {

            "message":

            "Upload API Working"

        }

    )

    if file.filename=="":


        return jsonify(

            {

                "error":

                "No file selected"

            }

        ),400


    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):

        return jsonify(

            {

                "error":

                "Only PDF (.pdf) and Word (.docx) files are supported"

            }

        ),400




    os.makedirs(

        "documents",

        exist_ok=True

    )

    safe_filename = secure_filename(file.filename)

    if not safe_filename:

        return jsonify(

            {

                "error":

                "Invalid file name"

            }

        ),400

    file_path = os.path.join(

        "documents",

        f"{uuid.uuid4().hex}_{safe_filename}"

    )



    file.save(

        file_path

    )



    file_size = os.path.getsize(

        file_path

    )



    collection_id = request.form.get("collection_id")

    if collection_id:

        try:

            collection_id = int(collection_id)

        except ValueError:

            return jsonify(

                {

                    "error":

                    "collection_id must be an integer"

                }

            ),400

    else:

        collection_id = None



    document_id = save_document(

        file.filename,

        file_path,

        file_size,

        0,

        collection_id

    )



    try:

        chunks = chunk_document(
            file_path
        )

    except Exception as e:

        mark_document_failed(
            document_id
        )

        return jsonify(
            {
                "error":
                str(e)
            }
        ),500

    save_chunks(
        document_id,
        chunks
    )

    set_total_chunks(
        document_id,
        len(chunks)
    )

    threading.Thread(
        target=run_ingestion_in_background,
        args=(document_id, chunks),
        daemon=True
    ).start()

    return jsonify(

        {

            "message":

            "Document uploaded, processing started",


            "document_id":

            document_id,


            "file_name":

            file.filename,


            "total_chunks":

            len(chunks),


            "status":

            "pending"

        }

    ),202


@document_bp.route(

    "/documents",

    methods=["GET"]

)
def list_documents():

    documents = get_all_documents()

    return jsonify(

        {

            "documents":

            documents

        }

    ),200


@document_bp.route(

    "/documents/<int:document_id>",

    methods=["GET"]

)
def get_document(
    document_id
):

    document = get_document_by_id(document_id)

    if not document:

        return jsonify(
            {
                "error":
                "Document not found"
            }
        ),404

    return jsonify(document),200


@document_bp.route(

    "/documents/<int:document_id>",

    methods=["DELETE"]

)
def remove_document(
    document_id
):

    document = get_document_by_id(document_id)

    if not document:

        return jsonify(

            {

                "error":

                "Document not found"

            }

        ),404

    delete_points_by_document(document_id)

    delete_chunks_by_document(document_id)

    delete_document(document_id)

    file_path = document.get("file_path")

    if file_path and os.path.exists(file_path):

        os.remove(file_path)

    return jsonify(

        {

            "message":

            "Document deleted"

        }

    ),200


@document_bp.route(

    "/collections",

    methods=["POST"]

)
def create_collection():

    data = request.get_json()

    name = data.get("name")

    if not name:

        return jsonify(

            {

                "error":

                "Collection name is required"

            }

        ),400

    collection_id = create_collection_record(name)

    return jsonify(

        {

            "id": collection_id,

            "name": name

        }

    ),200


@document_bp.route(

    "/collections",

    methods=["GET"]

)
def list_collections():

    return jsonify(

        get_all_collections()

    )


def make_snippet(text, query, context_chars=80):

    lower_text = text.lower()
    lower_query = query.lower()

    position = lower_text.find(lower_query)

    if position == -1:
        return text[:160] + ("..." if len(text) > 160 else "")

    start = max(0, position - context_chars)
    end = min(len(text), position + len(query) + context_chars)

    snippet = text[start:end]

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


@document_bp.route(

    "/search",

    methods=["GET"]

)
def search_documents():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    results = search_chunks(query)

    return jsonify(
        [
            {
                "document_id": row["document_id"],
                "file_name": row["file_name"],
                "chunk_index": row["chunk_index"],
                "snippet": make_snippet(row["chunk_text"], query)
            }
            for row in results
        ]
    )