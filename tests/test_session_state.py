import pytest
from app.session_state import (
    get_current_user,
    get_current_username,
    set_current_user,
    clear_session,
)
from app.domain import User


# fixture only for this module
# clean up session state before and after each test
@pytest.fixture(autouse=True)
def reset_session_state():
    clear_session()
    yield
    clear_session()


def test_set_current_user_success():
    """
    Setting a valid User should update the in-memory session
    and allow get_current_user / get_current_username to work.
    """
    user = User(
        username="alice",
        password="p",
        firstname="Alice",
        lastname="Liu",
        role="user",
        balance=0.0,
    )

    set_current_user(user)

    # same object instance
    assert get_current_user() is user
    assert get_current_username() == "alice"


def test_set_current_user_invalid_type_raises_type_error():
    """
    Passing a non-User object into set_current_user should
    trigger the TypeError branch in session_state.
    """
    with pytest.raises(TypeError):
        set_current_user("not_a_user")  # type: ignore[arg-type]


def test_clear_session_removes_user():
    """
    clear_session() should set the internal _current_user back to None.
    """
    user = User(
        username="bob",
        password="p",
        firstname="Bob",
        lastname="Zhang",
        role="user",
        balance=0.0,
    )
    set_current_user(user)

    clear_session()

    assert get_current_user() is None
    assert get_current_username() is None


def test_get_current_username_returns_none_when_no_user():
    """
    When no user is logged in, get_current_username() returns None,
    not raising errors.
    """
    # reset_session_state fixture clears session
    clear_session()
    assert get_current_username() is None
