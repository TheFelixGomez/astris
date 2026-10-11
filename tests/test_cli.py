from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from astris.cli import orbit_cli

runner = CliRunner()


def test_orbit_list():
    # Arrange
    from astris.cli import list_commands

    mock_ctx = MagicMock()
    mock_ctx.parent = None
    mock_ctx.get_help.return_value = "Help output"

    # Act
    result = runner.invoke(orbit_cli, ["list"])
    list_commands(mock_ctx)

    # Assert
    assert result.exit_code == 0
    assert "serve" in result.output
    assert "make:module" in result.output
    mock_ctx.get_help.assert_called_once()


def test_orbit_serve_with_vite_and_cleanup(tmp_path: Path, monkeypatch):
    # Arrange
    import subprocess
    import sys

    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "app").mkdir()
    (tmp_path / "database").mkdir()

    if str(tmp_path) in sys.path:
        sys.path.remove(str(tmp_path))

    # Act & Assert 1: Normal serve with Vite timeout cleanup
    with patch("subprocess.Popen") as mock_popen, patch("uvicorn.run"):
        mock_proc = MagicMock()
        mock_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="npm", timeout=2)
        mock_popen.return_value = mock_proc

        result = runner.invoke(orbit_cli, ["serve", "--port", "8000"])
        assert result.exit_code == 0
        mock_popen.assert_called_once()
        mock_proc.kill.assert_called_once()

    # Act & Assert 2: Vite process cleanup OSError
    with patch("subprocess.Popen") as mock_popen_os, patch("uvicorn.run"):
        mock_proc_os = MagicMock()
        mock_proc_os.wait.side_effect = OSError("Process already dead")
        mock_popen_os.return_value = mock_proc_os
        result_os = runner.invoke(orbit_cli, ["serve"])
        assert result_os.exit_code == 0

    # Act & Assert 3: Popen failure
    with (
        patch("subprocess.Popen", side_effect=OSError("npm not found")),
        patch("uvicorn.run"),
    ):
        result_err = runner.invoke(orbit_cli, ["serve"])
        assert result_err.exit_code == 0
        assert "Could not start Vite dev server" in result_err.output

    # Act & Assert 4: Serve without app/database directories (fallback reload_dirs)
    empty_dir = tmp_path / "empty_proj"
    empty_dir.mkdir()
    monkeypatch.chdir(empty_dir)
    with patch("uvicorn.run") as mock_uvicorn_empty:
        result_empty = runner.invoke(orbit_cli, ["serve"])
        assert result_empty.exit_code == 0
        _, kwargs = mock_uvicorn_empty.call_args
        assert kwargs["reload_dirs"] == [str(empty_dir)]


def test_orbit_serve_prod():
    # Arrange & Act
    with patch("uvicorn.run") as mock_uvicorn:
        result = runner.invoke(orbit_cli, ["serve", "--prod", "--workers", "2"])

        # Assert
        assert result.exit_code == 0
        mock_uvicorn.assert_called_once()
        _, kwargs = mock_uvicorn.call_args
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["workers"] == 2
        assert kwargs["reload"] is False


def test_orbit_make_module(tmp_path: Path):
    # Arrange
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        # Act
        res = runner.invoke(orbit_cli, ["make:module", "billing"])
        res_dup = runner.invoke(orbit_cli, ["make:module", "billing"])

        # Assert
        assert res.exit_code == 0
        assert "Created module 'app/modules/billing'" in res.output
        assert (
            tmp_path / "app" / "modules" / "billing" / "billing_controller.py"
        ).exists()
        assert (
            tmp_path / "app" / "modules" / "billing" / "billing_service.py"
        ).exists()
        assert (tmp_path / "app" / "modules" / "billing" / "billing_model.py").exists()
        assert res_dup.exit_code == 1
        assert "already exists" in res_dup.output


def test_orbit_make_controller(tmp_path: Path):
    # Arrange
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        # Act
        res = runner.invoke(
            orbit_cli, ["make:controller", "reports", "--module", "analytics"]
        )
        res_dup = runner.invoke(
            orbit_cli, ["make:controller", "reports", "--module", "analytics"]
        )

        # Assert
        assert res.exit_code == 0
        assert "Created app/modules/analytics/reports_controller.py" in res.output
        assert res_dup.exit_code == 1
        assert "already exists" in res_dup.output


def test_orbit_make_model(tmp_path: Path):
    # Arrange
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        # Act
        res = runner.invoke(orbit_cli, ["make:model", "Invoice", "--module", "billing"])
        res_dup = runner.invoke(
            orbit_cli, ["make:model", "Invoice", "--module", "billing"]
        )

        # Assert
        assert res.exit_code == 0
        assert "Created app/modules/billing/invoice_model.py" in res.output
        assert res_dup.exit_code == 1
        assert "already exists" in res_dup.output


def test_orbit_migrations():
    # Arrange
    with (
        patch("astris.database.migrations.create_migration") as mock_create,
        patch("astris.database.migrations.run_migrations") as mock_run,
        patch("astris.database.migrations.rollback_migrations") as mock_roll,
        patch("astris.database.migrations.get_migration_status") as mock_status,
    ):
        # Act & Assert 1: make:migration
        res1 = runner.invoke(orbit_cli, ["make:migration", "add_users"])
        assert res1.exit_code == 0
        mock_create.assert_called_once()

        mock_create.side_effect = RuntimeError("migration failed")
        res_err = runner.invoke(orbit_cli, ["make:migration", "bad"])
        assert res_err.exit_code == 1

        # Act & Assert 2: migrate
        res2 = runner.invoke(orbit_cli, ["migrate"])
        assert res2.exit_code == 0
        mock_run.assert_called_once()

        mock_run.side_effect = RuntimeError("migrate failed")
        res2_err = runner.invoke(orbit_cli, ["migrate"])
        assert res2_err.exit_code == 1

        # Act & Assert 3: migrate:rollback
        res3 = runner.invoke(orbit_cli, ["migrate:rollback", "--steps", "2"])
        assert res3.exit_code == 0
        mock_roll.assert_called_once()

        mock_roll.side_effect = RuntimeError("rollback failed")
        res3_err = runner.invoke(orbit_cli, ["migrate:rollback"])
        assert res3_err.exit_code == 1

        # Act & Assert 4: migrate:status
        mock_status.return_value = {
            "current_revisions": ["rev1"],
            "heads": ["rev1"],
            "is_up_to_date": True,
        }
        res4 = runner.invoke(orbit_cli, ["migrate:status"])
        assert res4.exit_code == 0
        assert "Database is up to date" in res4.output

        mock_status.return_value = {
            "current_revisions": [],
            "heads": ["rev2"],
            "is_up_to_date": False,
        }
        res4_pend = runner.invoke(orbit_cli, ["migrate:status"])
        assert res4_pend.exit_code == 0
        assert "Pending migrations exist" in res4_pend.output

        mock_status.side_effect = RuntimeError("status failed")
        res4_err = runner.invoke(orbit_cli, ["migrate:status"])
        assert res4_err.exit_code == 1


def test_orbit_key_generate(tmp_path: Path):
    # Arrange
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        env_file = tmp_path / ".env"

        # Act & Assert 1: Show only
        res_show = runner.invoke(orbit_cli, ["key:generate", "--show"])
        assert res_show.exit_code == 0
        assert "APP_KEY=" in res_show.output

        # Act & Assert 2: Write to new .env
        res_write = runner.invoke(orbit_cli, ["key:generate"])
        assert res_write.exit_code == 0
        assert env_file.exists()
        assert "APP_KEY=" in env_file.read_text(encoding="utf-8")

        # Act & Assert 3: Replace existing APP_KEY in .env
        env_file.write_text("APP_NAME=App\nAPP_KEY=old-key\n", encoding="utf-8")
        res_replace = runner.invoke(orbit_cli, ["key:generate"])
        assert res_replace.exit_code == 0
        assert "old-key" not in env_file.read_text(encoding="utf-8")

        # Act & Assert 4: APP_KEY= in content but not starting line
        env_file.write_text("# Note: APP_KEY=commented\nDEBUG=True\n", encoding="utf-8")
        res_comment = runner.invoke(orbit_cli, ["key:generate"])
        assert res_comment.exit_code == 0
        content = env_file.read_text(encoding="utf-8")
        assert content.count("APP_KEY=") == 2

        # Act & Assert 5: .env exists without APP_KEY
        env_file.write_text("DEBUG=True\n", encoding="utf-8")
        res_append = runner.invoke(orbit_cli, ["key:generate"])
        assert res_append.exit_code == 0
        assert "APP_KEY=" in env_file.read_text(encoding="utf-8")


def test_orbit_make_auth():
    # Arrange
    with patch("astris.auth.installer.install_auth_starter") as mock_install:
        # Act & Assert 1: Success
        res = runner.invoke(orbit_cli, ["make:auth", "--force"])
        assert res.exit_code == 0
        assert "Authentication and starter kit scaffolding generated" in res.output

        # Act & Assert 2: FileExistsError
        mock_install.side_effect = FileExistsError("Files exist")
        res_exist = runner.invoke(orbit_cli, ["make:auth"])
        assert res_exist.exit_code == 1
        assert "Error: Files exist" in res_exist.output

        # Act & Assert 3: Generic Exception
        mock_install.side_effect = RuntimeError("Unknown error")
        res_err = runner.invoke(orbit_cli, ["make:auth"])
        assert res_err.exit_code == 1


def test_orbit_skills_install_and_update(tmp_path: Path):
    # Arrange
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        # Act & Assert 1: Install with --claude
        res = runner.invoke(orbit_cli, ["skills:install", "--claude"])
        assert res.exit_code == 0
        assert "Astris AI skill installed successfully" in res.output
        assert (tmp_path / ".agents" / "skills" / "astris" / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "skills" / "astris" / "SKILL.md").exists()

        # Act & Assert 2: Update skills
        res_update = runner.invoke(orbit_cli, ["skills:update"])
        assert res_update.exit_code == 0

        # Act & Assert 3: Missing skill in package error
        with patch("pathlib.Path.exists", return_value=False):
            res_missing = runner.invoke(orbit_cli, ["skills:install"])
            assert res_missing.exit_code == 1
            assert "Error: Astris skill file not found in package" in res_missing.output


def test_orbit_make_docker(tmp_path: Path):
    # Arrange
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        # Act & Assert 1: Default (no Vercel)
        res = runner.invoke(orbit_cli, ["make:docker"])
        assert res.exit_code == 0
        assert "Production Docker files generated successfully" in res.output
        assert (tmp_path / "Dockerfile").exists()
        assert not (tmp_path / "Dockerfile.vercel").exists()
        assert (tmp_path / ".dockerignore").exists()

        # Act & Assert 2: FileExistsError without force
        res_exists = runner.invoke(orbit_cli, ["make:docker"])
        assert res_exists.exit_code == 1
        assert "Docker configuration files already exist" in res_exists.output

        # Act & Assert 3: Overwrite with force and --vercel
        res_force = runner.invoke(orbit_cli, ["make:docker", "--force", "--vercel"])
        assert res_force.exit_code == 0
        assert (tmp_path / "Dockerfile.vercel").exists()

        # Act & Assert 4: Collision when only Dockerfile.vercel exists
        (tmp_path / "Dockerfile").unlink()
        (tmp_path / ".dockerignore").unlink()
        res_vercel_collision = runner.invoke(orbit_cli, ["make:docker", "--vercel"])
        assert res_vercel_collision.exit_code == 1
        assert "Docker configuration files already exist" in res_vercel_collision.output
