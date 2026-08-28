from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.types import ASGIApp


class PublicStaticMiddleware(BaseHTTPMiddleware):
    """Serve physical static files directly from the public/ directory."""

    def __init__(self, app: ASGIApp, public_dir: Path) -> None:
        super().__init__(app)
        self.public_dir = public_dir

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method in ("GET", "HEAD"):
            raw_path = request.url.path.lstrip("/")
            if raw_path and not raw_path.startswith("build/"):
                file_path = (self.public_dir / raw_path).resolve()
                try:
                    if file_path.is_file() and file_path.is_relative_to(
                        self.public_dir
                    ):
                        return FileResponse(file_path)
                except (ValueError, OSError):
                    pass

        return await call_next(request)
