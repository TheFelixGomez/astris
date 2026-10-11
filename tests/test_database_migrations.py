from pathlib import Path
from unittest.mock import MagicMock, patch

from astris.database.migrations import (
    create_migration,
    discover_models,
    ensure_migration_setup,
    get_alembic_config,
    get_migration_status,
    rollback_migrations,
    run_env,
    run_migrations,
)


def test_ensure_migration_setup_and_discover_models(tmp_path: Path):
    # Arrange 1: Fresh setup
    # Act 1
    ini_path, migrations_dir = ensure_migration_setup(tmp_path)

    # Assert 1
    assert ini_path.exists()
    assert (migrations_dir / "env.py").exists()
    assert (migrations_dir / "script.py.mako").exists()
    assert (migrations_dir / "versions").exists()

    # Arrange 2: Re-run with existing custom config
    ini_path.write_text("# custom ini", encoding="utf-8")

    # Act 2
    ensure_migration_setup(tmp_path)

    # Assert 2
    assert ini_path.read_text(encoding="utf-8") == "# custom ini"

    # Arrange 3: Model discovery directories
    modules_dir = tmp_path / "app" / "modules"
    posts_dir = modules_dir / "posts"
    posts_dir.mkdir(parents=True)
    (tmp_path / "app" / "__init__.py").touch()
    (modules_dir / "__init__.py").touch()
    (posts_dir / "__init__.py").touch()
    (posts_dir / "posts_model.py").write_text("VALID_MODEL = True\n", encoding="utf-8")
    (posts_dir / "broken_model.py").write_text(
        "import non_existent_pkg_xyz\n", encoding="utf-8"
    )

    # Act 3
    discover_models(tmp_path / "empty")
    discover_models(tmp_path)


def test_alembic_config_and_commands(tmp_path: Path):
    # Arrange
    # Act
    cfg = get_alembic_config(tmp_path)

    # Assert
    assert cfg is not None
    assert cfg.get_main_option("script_location") is not None

    # Arrange & Act & Assert for revision, upgrade, downgrade commands
    with (
        patch("alembic.command.revision") as mock_rev,
        patch("alembic.command.upgrade") as mock_up,
        patch("alembic.command.downgrade") as mock_down,
    ):
        # Act
        create_migration("test initial", autogenerate=True, base_path=tmp_path)
        run_migrations("head", base_path=tmp_path)
        rollback_migrations("-1", base_path=tmp_path)

        # Assert
        mock_rev.assert_called_once()
        mock_up.assert_called_once()
        mock_down.assert_called_once()


def test_get_migration_status(tmp_path: Path):
    # Arrange
    with (
        patch("alembic.script.ScriptDirectory.from_config") as mock_script_dir,
        patch("alembic.runtime.migration.MigrationContext.configure") as mock_ctx_conf,
        patch("astris.database.session.db.engine.connect"),
    ):
        mock_script_instance = MagicMock()
        mock_script_instance.get_heads.return_value = ["rev1"]
        mock_script_dir.return_value = mock_script_instance

        mock_ctx = MagicMock()
        mock_ctx.get_current_heads.return_value = ["rev1"]
        mock_ctx_conf.return_value = mock_ctx

        # Act
        status = get_migration_status(tmp_path)

        # Assert
        assert status["current_revisions"] == ["rev1"]
        assert status["heads"] == ["rev1"]
        assert status["is_up_to_date"] is True


def test_run_env(tmp_path: Path):
    # Arrange 1: Offline mode
    with (
        patch("alembic.context.is_offline_mode", create=True, return_value=True),
        patch("alembic.context.config", create=True) as mock_cfg,
        patch("alembic.context.configure", create=True) as mock_configure,
        patch("alembic.context.begin_transaction", create=True),
        patch("alembic.context.run_migrations", create=True) as mock_run,
    ):
        mock_cfg.config_file_name = None
        mock_cfg.get_main_option.return_value = "sqlite:///database/app.db"

        # Act 1
        run_env(base_path=tmp_path)

        # Assert 1
        mock_configure.assert_called_once()
        mock_run.assert_called_once()

    # Arrange 2: Online mode with connectable in attributes
    mock_connectable = MagicMock()
    mock_connection = MagicMock()
    mock_connection.dialect.name = "sqlite"
    mock_connectable.connect.return_value.__enter__.return_value = mock_connection

    with (
        patch("alembic.context.is_offline_mode", create=True, return_value=False),
        patch("alembic.context.config", create=True) as mock_cfg,
        patch("alembic.context.configure", create=True) as mock_configure,
        patch("alembic.context.begin_transaction", create=True),
        patch("alembic.context.run_migrations", create=True) as mock_run,
    ):
        mock_cfg.config_file_name = None
        mock_cfg.attributes = {"connection": mock_connectable}

        # Act 2
        run_env(base_path=tmp_path)

        # Assert 2
        mock_configure.assert_called_once()
        mock_run.assert_called_once()

    # Arrange 3: Online mode with config_file_name and engine_from_config
    with (
        patch("alembic.context.is_offline_mode", create=True, return_value=False),
        patch("alembic.context.config", create=True) as mock_cfg,
        patch("alembic.context.configure", create=True) as mock_configure,
        patch("alembic.context.begin_transaction", create=True),
        patch("alembic.context.run_migrations", create=True) as mock_run,
        patch("logging.config.fileConfig") as mock_file_config,
        patch(
            "sqlalchemy.engine_from_config", return_value=mock_connectable
        ) as mock_eng_from_cfg,
    ):
        mock_cfg.config_file_name = "alembic.ini"
        mock_cfg.attributes = {}
        mock_cfg.config_ini_section = "alembic"
        mock_cfg.get_section.return_value = {}

        # Act 3
        run_env(base_path=tmp_path)

        # Assert 3
        mock_file_config.assert_called_once_with("alembic.ini")
        mock_eng_from_cfg.assert_called_once()
