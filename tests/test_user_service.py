# tests/test_user_service.py
import pytest
from app.domain import User, Portfolio
from app.service.user_service import (
    list_users,
    create_user,
    delete_user,
    authenticate,
    UnsupportedUserOperationError,
)

# ---------------------------------------------------------
#  list_users
# ---------------------------------------------------------
def test_list_users_returns_all(db_session):
    """list_users() should return all non-admin users in the DB."""
    db_session.add_all([
        User(username="test1", password="p", firstname="Test", lastname="One", balance=1000, role="user"),
        User(username="test2", password="p", firstname="Test", lastname="Two", balance=2000, role="user"),
    ])
    db_session.commit()

    users = list_users()
    # filter out the baseline admin inserted by _populate_database
    usernames = sorted(u.username for u in users if u.username != "admin")

    assert usernames == ["test1", "test2"]


# ---------------------------------------------------------
#  create_user
# ---------------------------------------------------------
def test_create_user_success(db_session):
    """Normal user creation should succeed."""
    new_user = User(
        username="newuser",
        password="123",
        firstname="New",
        lastname="User",
        balance=2000.0,
        role="user",
    )

    create_user(new_user)

    stored = db_session.get(User, "newuser")
    assert stored is not None
    assert stored.username == "newuser"


def test_create_user_fail_duplicate(db_session):
    """Creating a user with an existing username should fail."""
    # existing user in DB
    db_session.add(User(
        username="dupuser",
        password="p",
        firstname="Dup",
        lastname="Original",
        balance=3000,
        role="user",
    ))
    db_session.commit()

    # try to create another user with the SAME username
    new_user = User(
        username="dupuser",  # <-- must be the same
        password="123",
        firstname="Dup",
        lastname="Copy",
        balance=0,
        role="user",
    )

    with pytest.raises(ValueError):
        create_user(new_user)


def test_create_user_fail_admin_creation(db_session):
    """Creating an admin using create_user() should raise an error."""
    new_admin = User(
        username="newadmin",
        password="p",
        firstname="New",
        lastname="Admin",
        balance=4000,
        role="admin",
    )

    with pytest.raises(UnsupportedUserOperationError):
        create_user(new_admin)


# ---------------------------------------------------------
#  delete_user
# ---------------------------------------------------------
def test_delete_user_success(db_session):
    """Deleting a normal user with no portfolios should succeed."""
    user = User(
        username="user_to_delete",
        password="p",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(user)
    db_session.commit()

    # requester is an admin (we can just create a transient object)
    requester = User(
        username="admin",
        password="p",
        firstname="Adm",
        lastname="In",
        role="admin",
        balance=0,
    )

    delete_user("user_to_delete", requester=requester)

    assert db_session.get(User, "user_to_delete") is None


def test_delete_user_fail_self_delete(db_session):
    """A user cannot delete themselves."""
    me = User(
        username="meuser",
        password="p",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(me)
    db_session.commit()

    with pytest.raises(UnsupportedUserOperationError):
        delete_user("meuser", requester=me)


def test_delete_user_fail_nonexistent(db_session):
    """Deleting a user that doesn't exist should raise ValueError."""
    requester = User(
        username="admin",
        password="p",
        firstname="Adm",
        lastname="In",
        role="admin",
        balance=0,
    )

    with pytest.raises(ValueError):
        delete_user("ghost_user", requester=requester)


def test_delete_user_fail_last_admin(db_session):
    """Deleting the only admin should fail."""
    # admin already exists from _populate_database, just fetch it
    admin = db_session.get(User, "admin")
    assert admin is not None

    with pytest.raises(UnsupportedUserOperationError):
        delete_user("admin", requester=admin)


def test_delete_user_fail_user_has_portfolios(db_session):
    """Cannot delete a user who still owns portfolios."""
    u = User(
        username="portfolio_owner",
        password="p",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    db_session.add(Portfolio(
        name="P1",
        description="Test portfolio",
        owner="portfolio_owner",
    ))
    db_session.commit()

    requester = User(
        username="admin",
        password="p",
        firstname="Adm",
        lastname="In",
        role="admin",
        balance=0,
    )

    with pytest.raises(UnsupportedUserOperationError):
        delete_user("portfolio_owner", requester=requester)


# ---------------------------------------------------------
#  authenticate
# ---------------------------------------------------------
def test_authenticate_success(db_session):
    """authenticate() returns the user if credentials match."""
    u = User(
        username="loginuser",
        password="123",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    result = authenticate("loginuser", "123")
    assert result is not None
    assert result.username == "loginuser"


def test_authenticate_wrong_password(db_session):
    """authenticate() should return None for wrong password."""
    u = User(
        username="loginuser2",
        password="123",
        firstname="A",
        lastname="B",
        balance=0,
        role="user",
    )
    db_session.add(u)
    db_session.commit()

    assert authenticate("loginuser2", "wrong") is None


def test_authenticate_no_such_user(db_session):
    """authenticate() should return None if user doesn't exist."""
    assert authenticate("ghost_login", "123") is None
