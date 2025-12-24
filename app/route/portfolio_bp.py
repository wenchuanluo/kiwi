# app/route/portfolio_bp.py
from flask import Blueprint, request

from app.domain import User
from app.service.portfolio_service import (
    list_portfolios,
    get_portfolio,
    create_portfolio,
    delete_portfolio,
    buy_security,
    sell_security,
    PortfolioOperationError,
)

portfolio_bp = Blueprint("portfolio", __name__, url_prefix="/portfolios")


@portfolio_bp.route("", methods=["GET"])
def get_all_portfolios():
    """
    Get all portfolios.
    Optional query param: ?owner=username
    """
    try:
        owner = request.args.get("owner")
        portfolios = list_portfolios(owner_username=owner)

        data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "owner": p.owner,
            }
            for p in portfolios
        ]
        return {"portfolios": data}, 200
    except Exception as e:
        return {"error": str(e)}, 400


@portfolio_bp.route("/<int:portfolio_id>", methods=["GET"])
def get_portfolio_by_id(portfolio_id: int):
    """Get a single portfolio by ID."""
    try:
        portfolio = get_portfolio(portfolio_id)
        if portfolio is None:
            return {"error": f"Portfolio '{portfolio_id}' not found."}, 404

        data = {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "owner": portfolio.owner,
        }
        return {"portfolio": data}, 200
    except Exception as e:
        return {"error": str(e)}, 400


@portfolio_bp.route("", methods=["POST"])
def create_new_portfolio():
    """
    Create a new portfolio.
    Expected JSON body:
    {
        "owner": "username",
        "name": "Portfolio Name",
        "description": "Optional description"
    }
    """
    try:
        data = request.get_json()

        owner = data.get("owner")
        name = data.get("name")
        description = data.get("description")

        if not owner or not name:
            return {"error": "Missing required fields: owner, name."}, 400

        portfolio = create_portfolio(
            owner_username=owner,
            name=name,
            description=description,
        )

        return {
            "message": "Portfolio created successfully.",
            "portfolio_id": portfolio.id,
        }, 201

    except PortfolioOperationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 400


@portfolio_bp.route("/<int:portfolio_id>", methods=["DELETE"])
def delete_existing_portfolio(portfolio_id: int):
    """
    Delete a portfolio.
    Optional JSON body:
    {
        "requesting_username": "username"
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        requesting_username = data.get("requesting_username")

        requesting_user = None
        if requesting_username:
            requesting_user = User.query.get(requesting_username)

        delete_portfolio(
            portfolio_id=portfolio_id,
            requesting_user=requesting_user,
        )

        return {"message": "Portfolio deleted successfully."}, 200

    except PortfolioOperationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 400


@portfolio_bp.route("/<int:portfolio_id>/buy", methods=["POST"])
def buy_security_route(portfolio_id: int):
    """
    Buy a security into a portfolio.
    Expected JSON body:
    {
        "ticker": "AAPL",
        "quantity": 10,
        "price": 180,              # optional
        "requesting_username": "username"
    }
    """
    try:
        data = request.get_json()

        ticker = data.get("ticker")
        quantity = data.get("quantity")
        price = data.get("price")
        requesting_username = data.get("requesting_username")

        if not ticker or quantity is None:
            return {"error": "Missing required fields: ticker, quantity."}, 400

        result = buy_security(
            portfolio_id=portfolio_id,
            ticker=ticker,
            quantity=quantity,
            price=price,
            requesting_username=requesting_username,
        )

        return result, 200

    except PortfolioOperationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 400


@portfolio_bp.route("/<int:portfolio_id>/sell", methods=["POST"])
def sell_security_route(portfolio_id: int):
    """
    Sell (harvest) a security from a portfolio.
    Expected JSON body:
    {
        "ticker": "AAPL",
        "quantity": 5,
        "price": 185,              # optional
        "requesting_username": "username"
    }
    """
    try:
        data = request.get_json()

        ticker = data.get("ticker")
        quantity = data.get("quantity")
        price = data.get("price")
        requesting_username = data.get("requesting_username")

        if not ticker or quantity is None:
            return {"error": "Missing required fields: ticker, quantity."}, 400

        result = sell_security(
            portfolio_id=portfolio_id,
            ticker=ticker,
            quantity=quantity,
            price=price,
            requesting_username=requesting_username,
        )

        return result, 200

    except PortfolioOperationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 400
