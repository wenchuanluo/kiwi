# app/route/user_bp.py
from flask import Blueprint, request

from app.domain import User
from app.service.user_service import (
    list_users,
    create_user,
    delete_user,
)

user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.route("", methods=["GET"])
def get_all_users():
    try:
        users = list_users()
        data = [
            {
                "username": u.username,
                "firstname": u.firstname,
                "lastname": u.lastname,
                "balance": float(u.balance),
                "role": u.role,
            }
            for u in users
        ]
        return {"users": data}, 200
    except Exception as e:
        return {"error": str(e)}, 400


@user_bp.route("/<username>", methods=["GET"])
def get_user_by_id(username: str):
    try:
        users = list_users()
        user = next((u for u in users if u.username == username), None)
        if user is None:
            return {"error": f"User '{username}' not found."}, 404

        return {
            "user": {
                "username": user.username,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "balance": float(user.balance),
                "role": user.role,
            }
        }, 200
    except Exception as e:
        return {"error": str(e)}, 400


@user_bp.route("", methods=["POST"])
def create_new_user():
    try:
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        balance = data.get("balance", 0.0)

        if not username or not password or not firstname or not lastname:
            return {"error": "Missing required fields."}, 400

        user = User(
            username=username,
            password=password,
            firstname=firstname,
            lastname=lastname,
            balance=balance,
            role="user",
        )

        create_user(user)
        return {"message": f"User '{username}' created successfully."}, 201
    except Exception as e:
        return {"error": str(e)}, 400


@user_bp.route("/<username>", methods=["DELETE"])
def delete_existing_user(username: str):
    try:
        delete_user(username)
        return {"message": f"User '{username}' deleted successfully."}, 200
    except Exception as e:
        return {"error": str(e)}, 400
