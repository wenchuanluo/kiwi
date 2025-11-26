import pytest
from app.domain import User
from app.service import login_service
from app import session_state


# ---------------------------------------------------------
#  login()
# ---------------------------------------------------------

def test_login_success(db_session, monkeypatch):
    """login() should return the user when credentials are correct."""
    # Arrange
    u = User(
        username="login1",
        password="pw",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    # Act
    result = login_service.login("login1", "pw")

    # Assert
    assert result is not None
    assert result.username == "login1"


def test_login_wrong_password(db_session, monkeypatch):
    """login() should return None when password is incorrect."""
    u = User(
        username="login2",
        password="pw",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    assert login_service.login("login2", "wrong") is None


def test_login_no_such_user(db_session):
    """login() should return None when username does not exist."""
    assert login_service.login("ghost", "pw") is None


def test_login_sets_session_state(db_session):
    """login() should store the current user in session_state."""
    # Arrange
    u = User(
        username="login3",
        password="pw",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    # Act
    login_service.login("login3", "pw")

    # Assert
    current = session_state.get_current_user()
    assert current is not None
    assert current.username == "login3"


# ---------------------------------------------------------
#  logout()
# ---------------------------------------------------------

def test_logout_clears_session_state(db_session):
    """logout() should clear the session state."""
    # Arrange
    u = User(
        username="login4",
        password="pw",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    login_service.login("login4", "pw")
    assert session_state.get_current_user() is not None

    # Act
    login_service.logout()

    # Assert
    assert session_state.get_current_user() is None


# ---------------------------------------------------------
#  get_current_user()
# ---------------------------------------------------------

def test_get_current_user(db_session):
    """get_current_user() returns whatever is in session_state."""
    u = User(
        username="login5",
        password="pw",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    login_service.login("login5", "pw")

    assert login_service.get_current_user().username == "login5"
