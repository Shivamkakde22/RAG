from flask import Blueprint, request, jsonify
from app.services.ragas_evaluator import evaluate

evaluate_bp = Blueprint("evaluate", __name__)


@evaluate_bp.route("/evaluate", methods=["POST"])
def run_evaluation():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        answer = data.get("answer", "").strip()
        chunks = data.get("chunks", [])

        if not query or not answer:
            return jsonify({"error": "query and answer are required"}), 400

        result = evaluate(query, answer, chunks)
        return jsonify(result)

    except Exception as e:
        print("Evaluate error:", e)
        return jsonify({"error": str(e)}), 500
