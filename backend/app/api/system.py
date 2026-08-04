from flask import Blueprint, jsonify

from app.services.rate_limit_status import get_status

system_bp = Blueprint("system", __name__)


@system_bp.route("/system/llm-status", methods=["GET"])
def llm_status():
    return jsonify(get_status()), 200
