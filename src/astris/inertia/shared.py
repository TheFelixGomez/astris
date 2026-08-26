import inspect
import json
from collections.abc import Callable
from typing import Any
from urllib.parse import quote, unquote

from fastapi import Request
from starlette.datastructures import MutableHeaders
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Global registry for shared prop factories
_SHARED_PROPS: dict[str, Any] = {}


def share(
    key_or_dict: str | dict[str, Any] | Callable[[Request], dict[str, Any]],
    value: Any = None,
) -> None:
    """Register global shared props that will be injected into every Inertia response.

    Can be called with:
    - share("app_name", "My App")
    - share({"app_name": "My App", "version": "1.0.0"})
    - share(lambda request: {"auth": {"user": getattr(request.state, "user", None)}})
    """
    if callable(key_or_dict) and value is None:
        _SHARED_PROPS[f"__callable_{id(key_or_dict)}"] = key_or_dict
    elif isinstance(key_or_dict, dict):
        for k, v in key_or_dict.items():
            _SHARED_PROPS[str(k)] = v
    elif isinstance(key_or_dict, str):
        _SHARED_PROPS[key_or_dict] = value


def flash(
    target: Request | Response,
    category: str,
    message: str,
) -> None:
    """Flash a session message (e.g. 'success', 'error', 'info') to the next Inertia response."""
    if isinstance(target, Request):
        # Attach to request state for current response or session
        if not hasattr(target.state, "flash_messages"):
            target.state.flash_messages = {}
        target.state.flash_messages[category] = message

        if hasattr(target, "session"):
            session_flashes = target.session.get("_flash", {})
            session_flashes[category] = message
            target.session["_flash"] = session_flashes
    elif isinstance(target, Response):
        # Attach cookie-based flash for redirect responses
        cookie_flashes = {category: message}
        target.set_cookie(
            key="_inertia_flash",
            value=quote(json.dumps(cookie_flashes)),
            path="/",
            httponly=True,
            samesite="lax",
        )


class FlashMiddleware:
    """Middleware that persists request.state.flash_messages across redirect cycles."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                flashes = getattr(request.state, "flash_messages", None)
                if flashes and not hasattr(request, "session"):
                    headers = MutableHeaders(scope=message)
                    cookie_val = quote(json.dumps(flashes))
                    cookie_str = (
                        f"_inertia_flash={cookie_val}; Path=/; SameSite=lax; HttpOnly"
                    )
                    headers.append("set-cookie", cookie_str)
            await send(message)

        await self.app(scope, receive, send_wrapper)


async def resolve_shared_props(request: Request) -> dict[str, Any]:
    """Evaluate and resolve all global and request-scoped shared props."""
    user = getattr(request.state, "user", None)
    if user is None and hasattr(request, "session"):
        user = request.session.get("user_data")
        if user is None and "user_id" in request.session:
            user = {"id": request.session.get("user_id")}

    resolved: dict[str, Any] = {
        "errors": {},
        "flash": {},
        "auth": {"user": user},
    }

    # 1. Resolve global registry
    for key, val in _SHARED_PROPS.items():
        if key.startswith("__callable_") and callable(val):
            res = val(request)
            if inspect.isawaitable(res):
                res = await res
            if isinstance(res, dict):
                resolved.update(res)
        elif callable(val):
            res = val(request)
            if inspect.isawaitable(res):
                res = await res
            resolved[key] = res
        else:
            resolved[key] = val

    # 2. Resolve request.state shared props if set by middleware
    state_shared = getattr(request.state, "inertia_shared_props", None)
    if isinstance(state_shared, dict):
        resolved.update(state_shared)

    # 3. Resolve flash messages
    flash_messages: dict[str, str] = {}

    # Check request.state
    state_flashes = getattr(request.state, "flash_messages", None)
    if isinstance(state_flashes, dict):
        flash_messages.update(state_flashes)

    # Check session if available
    if hasattr(request, "session"):
        session_flashes = request.session.pop("_flash", None)
        if isinstance(session_flashes, dict):
            flash_messages.update(session_flashes)

    # Check cookie fallback
    cookie_flash = request.cookies.get("_inertia_flash")
    if cookie_flash:
        try:
            parsed = json.loads(unquote(cookie_flash))
            if isinstance(parsed, dict):
                flash_messages.update(parsed)
        except json.JSONDecodeError:
            pass

    resolved["flash"] = flash_messages

    # 4. Resolve session / cookie flashed validation errors
    errors: dict[str, Any] = {}
    if hasattr(request, "session"):
        session_errors = request.session.pop("_errors", None)
        if isinstance(session_errors, dict):
            errors.update(session_errors)

    state_errors = getattr(request.state, "errors", None)
    if isinstance(state_errors, dict):
        errors.update(state_errors)

    cookie_errors = request.cookies.get("_inertia_errors")
    if cookie_errors:
        try:
            parsed_errors = json.loads(unquote(cookie_errors))
            if isinstance(parsed_errors, dict):
                errors.update(parsed_errors)
        except json.JSONDecodeError:
            pass

    if errors:
        resolved["errors"] = errors

    return resolved
