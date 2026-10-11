from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from astris.installer import installer_cli

runner = CliRunner()


def test_astris_new_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    with (
        patch("subprocess.run") as mock_subproc,
        patch("astris.auth.installer.install_auth_starter") as mock_auth,
    ):
        # Act
        result = runner.invoke(
            installer_cli,
            ["new", "my_app", "--claude"],
            catch_exceptions=False,
        )

        # Assert
        assert result.exit_code == 0
        assert "Project my_app created successfully!" in result.output
        mock_auth.assert_called_once()
        assert mock_subproc.call_count >= 2

        created_dir = tmp_path / "my_app"
        assert (created_dir / "Dockerfile").exists()
        assert not (created_dir / "Dockerfile.vercel").exists()
        assert (created_dir / ".dockerignore").exists()


def test_astris_new_no_auth_and_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    with (
        patch("subprocess.run"),
        patch("astris.auth.installer.install_auth_starter") as mock_auth,
    ):
        # Act
        result = runner.invoke(
            installer_cli,
            ["new", "app_no_auth", "--no-auth", "--local", str(tmp_path)],
            catch_exceptions=False,
        )

        # Assert
        assert result.exit_code == 0
        mock_auth.assert_not_called()
        assert (tmp_path / "app_no_auth").exists()


def test_astris_new_directory_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)
    existing_dir = tmp_path / "already_exists_app"
    existing_dir.mkdir(exist_ok=True)

    # Act
    result = runner.invoke(
        installer_cli,
        ["new", "already_exists_app"],
    )

    # Assert
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_astris_cli_callback() -> None:
    # Arrange & Act
    result = runner.invoke(installer_cli, ["--help"])

    # Assert
    assert result.exit_code == 0
    assert "Astris Framework Installer" in result.output


def test_astris_new_package_resolution_and_favicon_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act & Assert 1: Fallback to astris-python when neither sibling nor parent exists
    with (
        patch("subprocess.run") as mock_subproc,
        patch("importlib.resources.files", side_effect=TypeError("Resource error")),
    ):
        result = runner.invoke(
            installer_cli,
            ["new", "fallback_app", "--no-auth"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        subproc_calls = [c[0][0] for c in mock_subproc.call_args_list]
        assert ["uv", "add", "astris-python"] in subproc_calls

    # Arrange 2: Sibling astris exists with pyproject.toml
    sibling_astris = tmp_path / "astris"
    sibling_astris.mkdir()
    (sibling_astris / "pyproject.toml").touch()

    # Act & Assert 2: Sibling astris dependency addition
    with patch("subprocess.run") as mock_subproc_sibling:
        result2 = runner.invoke(
            installer_cli,
            ["new", "sibling_app", "--no-auth"],
            catch_exceptions=False,
        )
        assert result2.exit_code == 0
        subproc_calls2 = [c[0][0] for c in mock_subproc_sibling.call_args_list]
        assert any(
            c[:2] == ["uv", "add"] and str(sibling_astris.resolve()) in c[2]
            for c in subproc_calls2
        )

    # Arrange 3: Parent astris exists (nested subdir execution)
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    monkeypatch.chdir(nested_dir)

    # Act & Assert 3: Parent astris dependency addition
    with patch("subprocess.run") as mock_subproc_parent:
        result3 = runner.invoke(
            installer_cli,
            ["new", "parent_app", "--no-auth"],
            catch_exceptions=False,
        )
        assert result3.exit_code == 0
        subproc_calls3 = [c[0][0] for c in mock_subproc_parent.call_args_list]
        assert any(
            c[:2] == ["uv", "add"] and str(sibling_astris.resolve()) in c[2]
            for c in subproc_calls3
        )
