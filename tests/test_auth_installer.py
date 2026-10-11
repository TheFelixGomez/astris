from pathlib import Path

import pytest

from astris.auth.installer import install_auth_starter


def test_install_auth_starter(tmp_path: Path):
    # Arrange 1: Fresh project path
    auth_dir = tmp_path / "app" / "modules" / "auth"
    tasks_dir = tmp_path / "app" / "modules" / "tasks"
    migrations_dir = tmp_path / "database" / "migrations" / "versions"
    auth_pages_dir = tmp_path / "resources" / "js" / "Pages" / "Auth"
    components_dir = tmp_path / "resources" / "js" / "Components"
    dashboard_file = tmp_path / "resources" / "js" / "Pages" / "Dashboard.vue"

    # Act 1: Initial installation
    install_auth_starter(base_path=tmp_path, force=False)

    # Assert 1
    assert (auth_dir / "auth_model.py").exists()
    assert (auth_dir / "auth_service.py").exists()
    assert (auth_dir / "auth_controller.py").exists()
    assert (tasks_dir / "task_model.py").exists()
    assert (tasks_dir / "task_service.py").exists()
    assert (tasks_dir / "task_controller.py").exists()
    assert (migrations_dir / "0001_initial_schema.py").exists()
    assert (auth_pages_dir / "Login.vue").exists()
    assert (auth_pages_dir / "Register.vue").exists()
    assert (components_dir / "AstrisLogo.vue").exists()
    assert dashboard_file.exists()

    # Act & Assert 2: Re running without force raises FileExistsError
    with pytest.raises(FileExistsError) as exc_info:
        install_auth_starter(base_path=tmp_path, force=False)
    assert "Use --force to overwrite" in str(exc_info.value)

    # Arrange 3: Modify existing files
    (auth_dir / "auth_model.py").write_text("# custom edit", encoding="utf-8")
    (components_dir / "AstrisLogo.vue").write_text(
        "<template>Custom Logo</template>", encoding="utf-8"
    )

    # Act 3: Run with force=True
    install_auth_starter(base_path=tmp_path, force=True)

    # Assert 3
    assert "# custom edit" not in (auth_dir / "auth_model.py").read_text(
        encoding="utf-8"
    )
    assert "<template>Custom Logo</template>" == (
        components_dir / "AstrisLogo.vue"
    ).read_text(encoding="utf-8")
