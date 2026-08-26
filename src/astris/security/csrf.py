import secrets
from collections.abc import Sequence
from typing import ClassVar

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CSRFMiddleware:
    """Cookie-to-header CSRF protection middleware.

    Sets an XSRF-TOKEN cookie on responses and validates the incoming
    X-XSRF-TOKEN (or X-CSRF-TOKEN) header against the cookie on state-changing requests.
    """

    SAFE_METHODS: ClassVar[frozenset[str]] = frozenset({"GET", "HEAD", "OPTIONS"})
    COOKIE_NAME: ClassVar[str] = "XSRF-TOKEN"
    HEADER_NAMES: ClassVar[tuple[str, ...]] = ("x-xsrf-token", "x-csrf-token")

    def __init__(
        self,
        app: ASGIApp,
        cookie_name: str = "XSRF-TOKEN",
        cookie_path: str = "/",
        cookie_domain: str | None = None,
        cookie_secure: bool = False,
        cookie_samesite: str = "lax",
        exempt_paths: Sequence[str] = (),
    ) -> None:
        self.app = app
        self.cookie_name = cookie_name
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        cookie_token = request.cookies.get(self.cookie_name)
        new_token: str | None = None

        if not cookie_token:
            cookie_token = secrets.token_urlsafe(32)
            new_token = cookie_token

        # Validate state-changing methods (POST, PUT, PATCH, DELETE)
        if request.method.upper() not in self.SAFE_METHODS and not self._is_exempt(
            request.url.path
        ):
            header_token = None
            for header_name in self.HEADER_NAMES:
                if header_name in request.headers:
                    header_token = request.headers[header_name]
                    break

            if (
                not header_token
                or not cookie_token
                or not secrets.compare_digest(header_token, cookie_token)
            ):
                response = JSONResponse(
                    status_code=419,
                    content={"message": "CSRF token mismatch or missing."},
                )
                await response(scope, receive, send)
                return

        if new_token is not None:
            token_str: str = new_token

            async def send_wrapper(message: Message) -> None:
                if message["type"] == "http.response.start":
                    headers = MutableHeaders(scope=message)
                    cookie_parts = [
                        f"{self.cookie_name}={token_str}",
                        f"Path={self.cookie_path}",
                        f"SameSite={self.cookie_samesite.capitalize()}",
                    ]
                    if self.cookie_domain:
                        cookie_parts.append(f"Domain={self.cookie_domain}")
                    if self.cookie_secure:
                        cookie_parts.append("Secure")

                    headers.append("set-cookie", "; ".join(cookie_parts))

                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
