# app/route/security_bp.py
from flask import Blueprint

from app.service.security_service import list_securities

security_bp = Blueprint("security", __name__, url_prefix="/securities")


@security_bp.route("", methods=["GET"])
def get_all_securities():
    try:
        securities = list_securities()
        return {"securities": securities}, 200
    except Exception as e:
        return {"error": str(e)}, 400
