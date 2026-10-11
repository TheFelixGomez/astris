from pathlib import Path

import pytest
from starlette.testclient import TestClient

from astris.kernel import Astris


def test_kernel_boot_and_docs(tmp_path: Path):
    # Arrange
    public_dir = tmp_path / "public"
    public_dir.mkdir()
    (public_dir / "favicon.ico").write_text("icon")

    app_instance = Astris(
        base_path=tmp_path,
        title="Custom Astris App",
        secret_key="secret-12345",
        enable_csrf=True,
        csrf_exempt_paths=["/api/exempt"],
        shared_props={"site": "Astris"},
        database_url="sqlite:///:memory:",
        auto_create_tables=True,
        docs_url="/api-docs",
        redoc_url="/api-redoc",
        docs_favicon_url="/custom-favicon.ico",
    )
    client = TestClient(app_instance)

    # Act
    res_docs = client.get("/api-docs")
    res_oauth = client.get("/docs/oauth2-redirect")
    res_redoc = client.get("/api-redoc")
    res_fav = client.get("/favicon.ico")
    res_build = client.get("/build/non-existent.js")

    # Assert
    assert res_docs.status_code == 200
    assert "Custom Astris App - Swagger UI" in res_docs.text
    assert "/custom-favicon.ico" in res_docs.text

    assert res_oauth.status_code == 200

    assert res_redoc.status_code == 200
    assert "Custom Astris App - ReDoc" in res_redoc.text

    assert res_fav.status_code == 200
    assert res_build.status_code == 404


def test_kernel_without_docs_and_no_csrf(tmp_path: Path):
    # Arrange
    with pytest.warns(UserWarning, match="No secret key configured"):
        app_instance = Astris(
            base_path=tmp_path,
            secret_key=None,
            enable_csrf=False,
            docs_url=None,
            redoc_url=None,
            swagger_ui_oauth2_redirect_url=None,
            database_url="sqlite:///:memory:",
            auto_create_tables=False,
        )
    client = TestClient(app_instance)

    # Act
    res_docs = client.get("/docs")
    res_redoc = client.get("/redoc")

    # Assert
    assert res_docs.status_code == 404
    assert res_redoc.status_code == 404


def test_kernel_module_discovery(tmp_path: Path):
    # Arrange
    import sys

    for key in list(sys.modules.keys()):
        if key == "app" or key.startswith("app."):
            del sys.modules[key]

    modules_dir = tmp_path / "app" / "modules"
    welcome_dir = modules_dir / "welcome"
    welcome_dir.mkdir(parents=True)
    (tmp_path / "app" / "__init__.py").touch()
    (modules_dir / "__init__.py").touch()
    (welcome_dir / "__init__.py").touch()

    controller_code = """from astris.routing import Controller

controller = Controller(prefix="/discovered")

@controller.get("/ping")
def ping():
    return {"message": "pong"}
"""
    (welcome_dir / "welcome_controller.py").write_text(
        controller_code, encoding="utf-8"
    )

    model_code = """from sqlmodel import SQLModel, Field

class DiscoveredItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
"""
    (welcome_dir / "item_model.py").write_text(model_code, encoding="utf-8")

    (welcome_dir / "broken_model.py").write_text(
        "import non_existent_pkg_12345\n", encoding="utf-8"
    )
    (welcome_dir / "utils.py").write_text("FOO = 'bar'\n", encoding="utf-8")

    app_instance = Astris(
        base_path=tmp_path,
        secret_key="secret-key-12345",
        database_url="sqlite:///:memory:",
        auto_create_tables=True,
    )
    client = TestClient(app_instance)

    # Act
    res = client.get("/discovered/ping")

    # Assert
    assert res.status_code == 200
    assert res.json() == {"message": "pong"}
