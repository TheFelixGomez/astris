from typing import Annotated, Any, NoReturn, Self

from fastapi import Depends, HTTPException, Request, status
from fastapi.params import Depends as DependsClass
from pwdlib import PasswordHash

# Modern Argon2id hasher (pwdlib 0.3.1 / OWASP standard)
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password using modern Argon2id with automatic salt generation."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an Argon2id hash."""
    try:
        return password_hash.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def verify_and_update_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify a password and return an updated hash if security parameters need upgrading."""
    try:
        return password_hash.verify_and_update(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False, None


def login_user(
    request: Request,
    user_or_id: Any,
    user_data: dict[str, Any] | None = None,
) -> None:
    """Authenticate a user by storing their ID and safe profile data in the signed session."""
    user_id: int | str | None = None
    extracted_data: dict[str, Any] = (
        user_data.copy() if isinstance(user_data, dict) else {}
    )

    # 1. If an SQLModel or object instance is passed
    if hasattr(user_or_id, "id"):
        user_id = user_or_id.id
        if not user_data:
            if hasattr(user_or_id, "model_dump"):
                raw_dict = user_or_id.model_dump()
            elif hasattr(user_or_id, "__dict__"):
                raw_dict = dict(user_or_id.__dict__)
            else:
                raw_dict = {"id": user_id}
            # Strip sensitive database fields like passwords/hashes from the session cookie
            extracted_data = {
                k: v
                for k, v in raw_dict.items()
                if not k.startswith("_")
                and k
                not in (
                    "hashed_password",
                    "password",
                    "secret",
                    "password_hash",
                )
            }
    # 2. If a dictionary is passed
    elif isinstance(user_or_id, dict):
        user_id = user_or_id.get("id")
        if not user_data:
            extracted_data = {
                k: v
                for k, v in user_or_id.items()
                if k
                not in (
                    "hashed_password",
                    "password",
                    "secret",
                    "password_hash",
                )
            }
    # 3. If a raw ID is passed
    elif isinstance(user_or_id, (int, str)):
        user_id = user_or_id

    if user_id is None:
        raise ValueError("Could not determine user_id from the provided user object.")

    if not hasattr(request, "session"):
        request.state.user_id = user_id
        if extracted_data:
            request.state.user = extracted_data
        return

    request.session["user_id"] = user_id
    if extracted_data:
        request.session["user_data"] = extracted_data


def logout_user(request: Request) -> None:
    """Terminate the current authenticated session."""
    if hasattr(request, "session"):
        request.session.pop("user_id", None)
        request.session.pop("user_data", None)
    if hasattr(request.state, "user_id"):
        delattr(request.state, "user_id")
    if hasattr(request.state, "user"):
        delattr(request.state, "user")


def get_user_id(request: Request) -> int | str | None:
    """Retrieve the current authenticated user ID from the session or request state."""
    if hasattr(request, "session"):
        uid = request.session.get("user_id")
        if uid is not None:
            return uid
    return getattr(request.state, "user_id", None)


def get_auth_user(request: Request) -> dict[str, Any] | None:
    """Retrieve the current authenticated user profile dictionary from the session or request state."""
    user = getattr(request.state, "user", None)
    if user is not None:
        if isinstance(user, dict):
            return user
        if hasattr(user, "model_dump"):
            return user.model_dump()
    if hasattr(request, "session"):
        user_data = request.session.get("user_data")
        if isinstance(user_data, dict):
            return user_data
        uid = request.session.get("user_id")
        if uid is not None:
            return {"id": uid}
    uid = getattr(request.state, "user_id", None)
    if uid is not None:
        return {"id": uid}
    return None


def is_authenticated(request: Request) -> bool:
    """Check if the current request is from an authenticated user."""
    return get_user_id(request) is not None


# --- Internal Challenge Handlers ---


def _unauthorized_challenge(request: Request, redirect_url: str = "/login") -> NoReturn:
    """Handle unauthenticated request via 303 redirects (Inertia/HTML) or 401 JSON."""
    is_inertia = request.headers.get("X-Inertia") == "true"
    accept = request.headers.get("accept", "")
    if is_inertia or "text/html" in accept:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": redirect_url},
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def _guest_challenge(request: Request, redirect_url: str = "/dashboard") -> None:
    """Redirect already authenticated users to the dashboard."""
    if is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": redirect_url},
        )


# --- Internal Callables for Dependency Injection ---


def _default_auth_id_dependency(request: Request) -> int | str:
    user_id = get_user_id(request)
    if user_id is None:
        _unauthorized_challenge(request, "/login")
    return user_id


def _default_auth_user_dependency(request: Request) -> dict[str, Any]:
    user = get_auth_user(request)
    if user is None:
        _unauthorized_challenge(request, "/login")
    return user


# --- Unified Guards ---


class _AuthRequiredGuard(DependsClass):
    """Authentication guard dependency.

    Usage:
        dependencies=[auth_required]
        dependencies=[auth_required(redirect_url="/custom-login")]
    """

    def __init__(self, redirect_url: str = "/login") -> None:
        def _dependency(request: Request) -> int | str:
            user_id = get_user_id(request)
            if user_id is None:
                _unauthorized_challenge(request, redirect_url)
            return user_id

        super().__init__(dependency=_dependency)

    def __call__(self, redirect_url: str = "/login", **kwargs: Any) -> Self:
        url = kwargs.get("redirect_url", redirect_url)
        return self.__class__(redirect_url=url)


class _GuestRequiredGuard(DependsClass):
    """Guest-only guard dependency.

    Usage:
        dependencies=[guest_required]
        dependencies=[guest_required(redirect_url="/custom-dashboard")]
    """

    def __init__(self, redirect_url: str = "/dashboard") -> None:
        def _dependency(request: Request) -> None:
            _guest_challenge(request, redirect_url)

        super().__init__(dependency=_dependency)

    def __call__(self, redirect_url: str = "/dashboard", **kwargs: Any) -> Self:
        url = kwargs.get("redirect_url", redirect_url)
        return self.__class__(redirect_url=url)


# Direct Router / Controller Guards:
auth_required = _AuthRequiredGuard()
guest_required = _GuestRequiredGuard()

# Direct Parameter Type Aliases:
AuthUser = Annotated[dict[str, Any], Depends(_default_auth_user_dependency)]
AuthUserId = Annotated[int | str, Depends(_default_auth_id_dependency)]
