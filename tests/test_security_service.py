import pytest
from app.domain import Security
from app.service import security_service


# ---------------------------------------------------------
# 1. list_securities()
# ---------------------------------------------------------
def test_list_securities_returns_all(db_session):
    """list_securities() should return all securities in marketplace format."""

    # prepare – add extra sample securities on top of baseline (AAPL, TSLA, LULU), which is aligned with real DB
    db_session.add_all([
        Security(ticker="AAA", issuer="AAA Corp", price=10.5),
        Security(ticker="BBB", issuer="BBB Ltd", price=20.0),
    ])
    db_session.commit()

    # execute
    result = security_service.list_securities()

    # Assert
    assert isinstance(result, list)
    # At least the 3 baseline + 2 new
    assert len(result) >= 5

    # Build a lookup by ticker so we don't depend on ordering
    by_ticker = {item["ticker"]: item for item in result}

    # Ensure AAA is present and correctly mapped
    assert "AAA" in by_ticker
    assert by_ticker["AAA"] == {
        "ticker": "AAA",
        "name": "AAA Corp",
        "reference_price": 10.5,
    }

    # Ensure BBB is present and correctly mapped
    assert "BBB" in by_ticker
    assert by_ticker["BBB"] == {
        "ticker": "BBB",
        "name": "BBB Ltd",
        "reference_price": 20.0,
    }


# ---------------------------------------------------------
# 2. buy_security() – wrapper test with mocking
# ---------------------------------------------------------
def test_buy_security_calls_portfolio_service(monkeypatch):
    """
    buy_security() should forward arguments to portfolio_service.buy_security().
    We mock portfolio_service.buy_security to avoid hitting real DB logic.
    """

    captured_args = {}

    def fake_buy_security(**kwargs):
        # capture arguments to verify forwarding
        captured_args.update(kwargs)
        return {"ok": True}

    # Monkeypatch the portfolio service method
    import app.service.portfolio_service as ps
    monkeypatch.setattr(ps, "buy_security", fake_buy_security)

    # execute
    result = security_service.buy_security(
        portfolio_id=7,
        ticker="AAPL",
        quantity=2,
        price=150.0,
        requesting_username="alice"
    )

    # Assert result passthrough
    assert result == {"ok": True}

    # Assert forwarding arguments correctly
    assert captured_args == {
        "portfolio_id": 7,
        "ticker": "AAPL",
        "quantity": 2,
        "price": 150.0,
        "requesting_username": "alice",
    }
