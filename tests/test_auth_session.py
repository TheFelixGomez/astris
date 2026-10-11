import pytest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.datastructures import State
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.testclient import TestClient

from astris.auth.session import (
    AuthUser,
    AuthUserId,
    _default_auth_id_dependency,
    _default_auth_user_dependency,
    _guest_challenge,
    _unauthorized_challenge,
    auth_required,
    get_auth_user,
    get_user_id,
    guest_required,
    hash_password,
    is_authenticated,
    login_user,
    logout_user,
    verify_and_update_password,
    verify_password,
)


def test_password_hashing():
    # Arrange
    raw_password = "secret123"

    # Act
    hashed = hash_password(raw_password)
    valid = verify_password(raw_password, hashed)
    invalid = verify_password("wrong", hashed)
    invalid_format = verify_password(raw_password, "invalid-hash-format")
    valid_update, new_hash = verify_and_update_password(raw_password, hashed)
    invalid_update, bad_new_hash = verify_and_update_password(
        raw_password, "invalid-hash-format"
    )

    # Assert
    assert hashed != raw_password
    assert valid is True
    assert invalid is False
    assert invalid_format is False
    assert valid_update is True
    assert new_hash is None or isinstance(new_hash, str)
    assert invalid_update is False
    assert bad_new_hash is None


class DummyModel(BaseModel):
    id: int
    email: str
    hashed_password: str
    password: str
    secret: str


class DummyObjWithDict:
    def __init__(self, id: int, name: str, secret: str) -> None:
        self.id = id
        self.name = name
        self.secret = secret
        self._private = "hidden"


class DummyObjOnlyId:
    def __init__(self, id: int) -> None:
        self.id = id


def test_login_user_variants():
    # Arrange
    req = Request({"type": "http", "session": {}})
    model = DummyModel(
        id=42, email="test@example.com", hashed_password="h", password="p", secret="s"
    )

    req2 = Request({"type": "http", "session": {}})
    obj = DummyObjWithDict(id=99, name="Alice", secret="topsecret")

    req3 = Request({"type": "http", "session": {}})
    obj_id_only = DummyObjOnlyId(123)

    class ObjSlotsOnly:
        __slots__ = ("id",)

        def __init__(self, id: int) -> None:
            self.id = id

    req3b = Request({"type": "http", "session": {}})
    obj_slots = ObjSlotsOnly(456)

    req4 = Request({"type": "http", "session": {}})
    user_dict = {"id": 55, "name": "Bob", "hashed_password": "x"}

    req5 = Request({"type": "http", "session": {}})

    req6 = Request({"type": "http"})

    # Act
    login_user(req, model)
    login_user(req2, obj)
    login_user(req3, obj_id_only)
    login_user(req3b, obj_slots)
    login_user(req4, user_dict)
    login_user(req5, 100, user_data={"role": "admin"})
    login_user(req6, 200, user_data={"role": "editor"})

    # Assert
    assert req.session["user_id"] == 42
    assert req.session["user_data"] == {"id": 42, "email": "test@example.com"}

    assert req2.session["user_id"] == 99
    assert req2.session["user_data"] == {"id": 99, "name": "Alice"}

    assert req3.session["user_id"] == 123
    assert req3.session["user_data"] == {"id": 123}

    assert req3b.session["user_id"] == 456
    assert req3b.session["user_data"] == {"id": 456}

    assert req4.session["user_id"] == 55
    assert req4.session["user_data"] == {"id": 55, "name": "Bob"}

    assert req5.session["user_id"] == 100
    assert req5.session["user_data"] == {"role": "admin"}

    assert getattr(req6.state, "user_id", None) == 200
    assert getattr(req6.state, "user", None) == {"role": "editor"}

    with pytest.raises(ValueError):
        login_user(req, {"no_id": True})


def test_logout_and_helpers():
    # Arrange
    req = Request(
        {
            "type": "http",
            "session": {"user_id": 10, "user_data": {"id": 10, "name": "Test"}},
        }
    )
    req.state.user_id = 10
    req.state.user = {"id": 10}

    # Act & Assert 1: Initial auth state
    assert is_authenticated(req) is True
    assert get_user_id(req) == 10
    assert get_auth_user(req) == {"id": 10}

    # Act & Assert 2: Model user priority
    req.state.user = DummyModel(
        id=10, email="m@ex.com", hashed_password="h", password="p", secret="s"
    )
    auth_user = get_auth_user(req)
    assert auth_user is not None and auth_user["email"] == "m@ex.com"

    # Act & Assert 3: Logout
    logout_user(req)
    assert is_authenticated(req) is False
    assert get_user_id(req) is None
    assert get_auth_user(req) is None

    # Act & Assert 4: Session fallback with user_id only
    req_only_id = Request(
        {
            "type": "http",
            "session": {"user_id": 10},
        }
    )
    assert get_auth_user(req_only_id) == {"id": 10}

    # Act & Assert 5: State user_id only
    req_state_only = Request({"type": "http"})
    req_state_only.state.user_id = 77
    assert get_auth_user(req_state_only) == {"id": 77}

    # Act & Assert 6: Read-only state attributes
    class ReadOnlyState(State):
        @property
        def user_id(self) -> int:
            return 1

        @property
        def user(self) -> dict[str, str]:
            return {}

    class ReadOnlyRequest(Request):
        def __init__(self) -> None:
            super().__init__({"type": "http"})
            self._custom_state = ReadOnlyState()

        @property
        def state(self) -> State:
            return self._custom_state

    req_ro = ReadOnlyRequest()
    logout_user(req_ro)


def test_challenges_and_guards():
    # Arrange
    scope_inertia = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"x-inertia", b"true")],
    }
    req_inertia = Request(scope_inertia)

    scope_html = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"accept", b"text/html,application/xhtml+xml")],
    }
    req_html = Request(scope_html)

    scope_api = {
        "type": "http",
        "method": "GET",
        "path": "/api",
        "headers": [(b"accept", b"application/json")],
    }
    req_api = Request(scope_api)

    scope_guest = {
        "type": "http",
        "method": "GET",
        "path": "/login",
        "headers": [],
        "session": {"user_id": 1},
    }
    req_guest = Request(scope_guest)

    # Act & Assert 1: Inertia challenge
    with pytest.raises(HTTPException) as exc1:
        _unauthorized_challenge(req_inertia, "/login")
    assert exc1.value.status_code == 303
    assert exc1.value.headers and exc1.value.headers["Location"] == "/login"

    # Act & Assert 2: HTML challenge
    with pytest.raises(HTTPException) as exc2:
        _unauthorized_challenge(req_html, "/login")
    assert exc2.value.status_code == 303

    # Act & Assert 3: API challenge
    with pytest.raises(HTTPException) as exc3:
        _unauthorized_challenge(req_api, "/login")
    assert exc3.value.status_code == 401

    # Act & Assert 4: Default dependency challenges
    with pytest.raises(HTTPException) as exc_dep1:
        _default_auth_id_dependency(req_api)
    assert exc_dep1.value.status_code == 401

    with pytest.raises(HTTPException) as exc_dep2:
        _default_auth_user_dependency(req_api)
    assert exc_dep2.value.status_code == 401

    # Act & Assert 5: Guest challenge
    with pytest.raises(HTTPException) as exc4:
        _guest_challenge(req_guest, "/dashboard")
    assert exc4.value.status_code == 303
    assert exc4.value.headers and exc4.value.headers["Location"] == "/dashboard"


def test_guards_in_fastapi():
    # Arrange
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    @app.post("/login")
    def do_login(request: Request):
        login_user(request, {"id": 1, "name": "User 1"})
        return {"status": "logged_in"}

    @app.get("/protected", dependencies=[auth_required])
    def protected(user: AuthUser, uid: AuthUserId):
        return {"user": user, "uid": uid}

    @app.get(
        "/custom-protected", dependencies=[auth_required(redirect_url="/custom-login")]
    )
    def custom_protected():
        return {"ok": True}

    @app.get(
        "/guest-only", dependencies=[guest_required(redirect_url="/custom-dashboard")]
    )
    def guest_only():
        return {"guest": True}

    client = TestClient(app)

    # Act & Assert 1: Unauthenticated request to protected endpoint returns 401 JSON
    res_prot = client.get("/protected")
    assert res_prot.status_code == 401

    # Act & Assert 2: Inertia redirect for custom protected route
    res_custom = client.get(
        "/custom-protected", headers={"X-Inertia": "true"}, follow_redirects=False
    )
    assert res_custom.status_code == 303
    assert res_custom.headers["location"] == "/custom-login"

    # Act & Assert 3: Guest allowed when unauthenticated
    res_guest = client.get("/guest-only")
    assert res_guest.status_code == 200

    # Act & Assert 4: Login
    res_login = client.post("/login")
    assert res_login.status_code == 200

    # Act & Assert 5: Protected endpoint allowed when authenticated
    res_prot_ok = client.get("/protected")
    assert res_prot_ok.status_code == 200
    assert res_prot_ok.json() == {
        "user": {"id": 1, "name": "User 1"},
        "uid": 1,
    }

    # Act & Assert 6: Guest redirected when authenticated
    res_guest_authed = client.get("/guest-only", follow_redirects=False)
    assert res_guest_authed.status_code == 303
    assert res_guest_authed.headers["location"] == "/custom-dashboard"
