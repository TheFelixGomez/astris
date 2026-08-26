import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from astris.database.session import db

ENV_PY_TEMPLATE = """from astris.database.migrations import run_env

run_env()
"""

SCRIPT_MAKO_TEMPLATE = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade schema."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade schema."""
    ${downgrades if downgrades else "pass"}
'''

ALEMBIC_INI_TEMPLATE = """[alembic]
script_location = database/migrations
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""


def discover_models(base_path: Path | None = None) -> None:
    """Discover and import all domain model files to populate SQLModel.metadata."""
    root = base_path or Path.cwd()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    modules_dir = root / "app" / "modules"
    if not modules_dir.exists():
        return

    for _, modname, ispkg in pkgutil.walk_packages(
        [str(modules_dir)], prefix="app.modules."
    ):
        if ispkg:
            continue
        last_part = modname.split(".")[-1]
        if last_part.endswith(("_model", "_models")) or last_part in (
            "models",
            "model",
        ):
            try:
                importlib.import_module(modname)
            except ImportError:
                pass


def ensure_migration_setup(base_path: Path | None = None) -> tuple[Path, Path]:
    """Ensure alembic.ini and database/migrations/ directory structure exist."""
    root = base_path or Path.cwd()
    ini_path = root / "alembic.ini"
    migrations_dir = root / "database" / "migrations"
    versions_dir = migrations_dir / "versions"

    migrations_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)

    if not ini_path.exists():
        ini_path.write_text(ALEMBIC_INI_TEMPLATE, encoding="utf-8")

    env_path = migrations_dir / "env.py"
    if not env_path.exists():
        env_path.write_text(ENV_PY_TEMPLATE, encoding="utf-8")

    mako_path = migrations_dir / "script.py.mako"
    if not mako_path.exists():
        mako_path.write_text(SCRIPT_MAKO_TEMPLATE, encoding="utf-8")

    return ini_path, migrations_dir


def get_alembic_config(base_path: Path | None = None) -> Config:
    """Create and configure an Alembic Config object."""
    root = base_path or Path.cwd()
    ini_path, migrations_dir = ensure_migration_setup(root)

    discover_models(root)

    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(migrations_dir))
    cfg.set_main_option("sqlalchemy.url", db.url)
    return cfg


def create_migration(
    message: str,
    autogenerate: bool = True,
    base_path: Path | None = None,
) -> None:
    """Generate a new database migration file."""
    cfg = get_alembic_config(base_path)
    command.revision(cfg, message=message, autogenerate=autogenerate)


def run_migrations(
    revision: str = "head",
    base_path: Path | None = None,
) -> None:
    """Apply database migrations up to the target revision (default: 'head')."""
    cfg = get_alembic_config(base_path)
    command.upgrade(cfg, revision)


def rollback_migrations(
    revision: str = "-1",
    base_path: Path | None = None,
) -> None:
    """Roll back database migrations down to the target revision (default: '-1')."""
    cfg = get_alembic_config(base_path)
    command.downgrade(cfg, revision)


def get_migration_status(base_path: Path | None = None) -> dict[str, Any]:
    """Retrieve the current migration revision and available heads."""
    cfg = get_alembic_config(base_path)
    script_dir = ScriptDirectory.from_config(cfg)
    with db.engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_revs = context.get_current_heads()
        heads = script_dir.get_heads()

    return {
        "current_revisions": list(current_revs),
        "heads": list(heads),
        "is_up_to_date": set(current_revs) == set(heads),
    }


def run_env(
    target_metadata: Any = None,
    base_path: Path | None = None,
) -> None:
    """Run migrations in offline or online mode.

    Executed by database/migrations/env.py during Alembic migration runs.
    """
    from logging.config import fileConfig

    from alembic import context
    from sqlalchemy import engine_from_config, pool

    from astris.database import SQLModel

    root = base_path or Path.cwd()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    discover_models(root)

    config = context.config

    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    metadata = target_metadata if target_metadata is not None else SQLModel.metadata

    if context.is_offline_mode():
        url = config.get_main_option("sqlalchemy.url")
        is_sqlite = url and url.startswith("sqlite")
        context.configure(
            url=url,
            target_metadata=metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            render_as_batch=bool(is_sqlite),
        )

        with context.begin_transaction():
            context.run_migrations()
    else:
        connectable = config.attributes.get("connection", None)
        if connectable is None:
            connectable = engine_from_config(
                config.get_section(config.config_ini_section, {}),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )

        with connectable.connect() as connection:
            is_sqlite = connection.dialect.name == "sqlite"
            context.configure(
                connection=connection,
                target_metadata=metadata,
                render_as_batch=is_sqlite,
            )

            with context.begin_transaction():
                context.run_migrations()
