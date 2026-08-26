import importlib
import inspect
import pkgutil
import sys
from collections.abc import Callable, Coroutine, Sequence
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from astris.config import Settings, settings
from astris.database import db
from astris.inertia import share
from astris.inertia.exceptions import (
    inertia_http_exception_handler,
    inertia_validation_exception_handler,
)
from astris.inertia.shared import FlashMiddleware
from astris.security import CSRFMiddleware


class Astris:
    """Core framework application class."""

    def __init__(
        self,
        base_path: Path | None = None,
        config: Settings | None = None,
        title: str | None = None,
        cors_origins: Sequence[str] | None = None,
        enable_csrf: bool | None = None,
        csrf_exempt_paths: Sequence[str] | None = None,
        shared_props: dict[str, Any] | None = None,
        database_url: str | None = None,
        auto_create_tables: bool | None = None,
        db_echo: bool | None = None,
        secret_key: str | None = None,
        session_cookie_name: str | None = None,
        session_max_age: int | None = None,
        session_https_only: bool | None = None,
        session_same_site: Literal["lax", "strict", "none"] | None = None,
        **fastapi_kwargs: Any,
    ):
        self.base_path = base_path or Path.cwd()
        self.config = config or settings

        self.cors_origins: Sequence[str] = (
            cors_origins if cors_origins is not None else self.config.cors_origins
        )
        self.enable_csrf = (
            enable_csrf if enable_csrf is not None else self.config.enable_csrf
        )
        self.csrf_exempt_paths: Sequence[str] = (
            csrf_exempt_paths
            if csrf_exempt_paths is not None
            else self.config.csrf_exempt_paths
        )
        self.auto_create_tables = (
            auto_create_tables
            if auto_create_tables is not None
            else self.config.auto_create_tables
        )
        self.secret_key = secret_key or self.config.app_key
        self.session_cookie_name = (
            session_cookie_name or self.config.session_cookie_name
        )
        self.session_max_age = (
            session_max_age
            if session_max_age is not None
            else self.config.session_max_age
        )
        self.session_https_only = (
            session_https_only
            if session_https_only is not None
            else self.config.session_https_only
        )
        self.session_same_site = (
            session_same_site or self.config.session_same_site  # type: ignore[assignment]
        )

        # Configure database engine
        db.configure(
            url=database_url or self.config.database_url,
            echo=db_echo if db_echo is not None else self.config.db_echo,
            base_path=self.base_path,
        )

        if shared_props:
            share(shared_props)

        # Ensure project root is in sys.path for dynamic imports
        base_path_str = str(self.base_path)
        if base_path_str not in sys.path:
            sys.path.insert(0, base_path_str)

        app_title = title or self.config.app_name
        app_debug = self.config.app_debug
        self.app = FastAPI(title=app_title, debug=app_debug, **fastapi_kwargs)
        self._boot()

    def _boot(self) -> None:
        self._configure_middleware()
        self._configure_exception_handlers()
        self._mount_static()
        self._discover_modules()
        if self.auto_create_tables:
            db.create_all()

    def _configure_exception_handlers(self) -> None:
        """Register Inertia validation and HTTP exception handlers."""
        self.app.add_exception_handler(
            RequestValidationError,
            inertia_validation_exception_handler,
        )
        self.app.add_exception_handler(
            ValidationError,
            inertia_validation_exception_handler,
        )
        self.app.add_exception_handler(
            HTTPException,
            inertia_http_exception_handler,
        )
        self.app.add_exception_handler(
            StarletteHTTPException,
            inertia_http_exception_handler,
        )

    def _configure_middleware(self) -> None:
        """Register middleware stack (configured innermost to outermost)."""
        # 1. CSRF protection (innermost HTTP security)
        if self.enable_csrf:
            self.app.add_middleware(
                CSRFMiddleware,
                exempt_paths=self.csrf_exempt_paths,
            )

        # 2. Flash message persistence
        self.app.add_middleware(FlashMiddleware)

        # 3. Encrypted/signed cookie sessions
        if self.secret_key:
            self.app.add_middleware(
                SessionMiddleware,
                secret_key=self.secret_key,
                session_cookie=self.session_cookie_name,
                max_age=self.session_max_age,
                https_only=self.session_https_only,
                same_site=self.session_same_site,
            )

        # 4. CORS configuration (outermost to handle preflight)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=list(self.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Inertia", "X-XSRF-TOKEN"],
        )

    def _mount_static(self) -> None:
        """Mount compiled Vite frontend assets."""
        build_dir = self.base_path / "public" / "build"
        build_dir.mkdir(parents=True, exist_ok=True)
        self.app.mount(
            "/build",
            StaticFiles(directory=str(build_dir), check_dir=False),
            name="build",
        )

    def _discover_modules(self) -> None:
        modules_dir = self.base_path / "app" / "modules"
        if not modules_dir.exists():
            return

        registered_routers: set[int] = set()

        for _, modname, ispkg in pkgutil.walk_packages(
            [str(modules_dir)], prefix="app.modules."
        ):
            if ispkg:
                continue

            last_part = modname.split(".")[-1]

            # Auto-import models to register SQLModel table metadata
            if last_part.endswith(("_model", "_models")) or last_part in (
                "models",
                "model",
            ):
                try:
                    importlib.import_module(modname)
                except ImportError:
                    pass

            # Only scan controller files
            if not last_part.endswith("_controller") and not last_part.startswith(
                "controller"
            ):
                continue

            module = importlib.import_module(modname)
            for _, member in inspect.getmembers(module):
                if (
                    isinstance(member, APIRouter)
                    and id(member) not in registered_routers
                ):
                    self.app.include_router(member)
                    registered_routers.add(id(member))

    async def __call__(
        self,
        scope: Any,
        receive: Callable[..., Coroutine[Any, Any, Any]],
        send: Callable[..., Coroutine[Any, Any, None]],
    ) -> None:
        """ASGI 3 interface."""
        await self.app(scope, receive, send)
