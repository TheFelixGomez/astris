from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine


class Database:
    """Manages the SQLModel engine and session lifecycle."""

    def __init__(
        self,
        url: str | None = None,
        echo: bool = False,
        base_path: Path | None = None,
        **engine_kwargs: Any,
    ) -> None:
        self._url = url
        self._echo = echo
        self._base_path = base_path or Path.cwd()
        self._engine_kwargs = engine_kwargs
        self._engine: Engine | None = None

    @property
    def url(self) -> str:
        if self._url:
            return self._url
        from astris.config import get_settings

        config_url = get_settings().database_url
        if config_url:
            return config_url

        # Default to SQLite at database/app.db
        db_dir = self._base_path / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "app.db"
        return f"sqlite:///{db_path}"

    @property
    def engine(self) -> Engine:
        if self._engine is not None:
            return self._engine

        connect_args: dict[str, Any] = {}
        if self.url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        kwargs = {**self._engine_kwargs}
        if connect_args:
            kwargs["connect_args"] = {
                **connect_args,
                **kwargs.get("connect_args", {}),
            }

        engine = create_engine(self.url, echo=self._echo, **kwargs)
        self._engine = engine
        return engine

    def configure(
        self,
        url: str | None = None,
        echo: bool = False,
        base_path: Path | None = None,
        **engine_kwargs: Any,
    ) -> None:
        """Reconfigure database settings and reset the engine."""
        self._url = url
        self._echo = echo
        if base_path:
            self._base_path = base_path
        self._engine_kwargs = engine_kwargs
        self._engine = None

    def create_all(self) -> None:
        """Create all registered SQLModel tables."""
        SQLModel.metadata.create_all(self.engine)

    def drop_all(self) -> None:
        """Drop all registered SQLModel tables."""
        SQLModel.metadata.drop_all(self.engine)

    def get_session(self) -> Generator[Session]:
        """FastAPI dependency yielding a Session."""
        with Session(self.engine) as session:
            yield session

    @contextmanager
    def session(self) -> Generator[Session]:
        """Context manager yielding a Session for background tasks, CLI, and scripts."""
        with Session(self.engine) as session:
            yield session


# Global default database instance
db = Database()


def get_session() -> Generator[Session]:
    """Astris dependency that yields a database session."""
    yield from db.get_session()


# First-class dependency injection alias for route & controller handlers
DatabaseSession = Annotated[Session, Depends(get_session)]
