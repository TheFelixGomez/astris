from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from astris.http.static import PublicStaticMiddleware


def test_public_static_middleware(tmp_path: Path):
    # Arrange
    public_dir = tmp_path / "public"
    public_dir.mkdir()

    favicon = public_dir / "favicon.ico"
    favicon.write_text("fake-icon")

    robots = public_dir / "robots.txt"
    robots.write_text("User-agent: *")

    nested = public_dir / "images" / "logo.png"
    nested.parent.mkdir()
    nested.write_text("fake-logo")

    outside = tmp_path / "secret.txt"
    outside.write_text("secret")

    async def homepage(request: Request) -> PlainTextResponse:
        _ = request
        return PlainTextResponse("Home")

    async def build_asset(request: Request) -> PlainTextResponse:
        _ = request
        return PlainTextResponse("Built")

    app = Starlette(
        routes=[
            Route("/", homepage),
            Route("/build/bundle.js", build_asset),
        ]
    )
    app.add_middleware(PublicStaticMiddleware, public_dir=public_dir)
    client = TestClient(app)

    # Act
    res_fav = client.get("/favicon.ico")
    res_rob = client.get("/robots.txt")
    res_nested = client.get("/images/logo.png")
    res_head = client.head("/favicon.ico")
    res_build = client.get("/build/bundle.js")
    res_home = client.get("/")
    res_404 = client.get("/missing.txt")
    res_post = client.post("/favicon.ico")
    res_traversal = client.get("/../secret.txt")

    # Assert
    assert res_fav.status_code == 200
    assert res_fav.text == "fake-icon"

    assert res_rob.status_code == 200
    assert res_rob.text == "User-agent: *"

    assert res_nested.status_code == 200
    assert res_nested.text == "fake-logo"

    assert res_head.status_code == 200

    assert res_build.status_code == 200
    assert res_build.text == "Built"

    assert res_home.status_code == 200
    assert res_home.text == "Home"

    assert res_404.status_code == 404
    assert res_post.status_code == 404
    assert res_traversal.status_code == 404


def test_public_static_middleware_os_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    public_dir = tmp_path / "public"
    public_dir.mkdir()

    app = Starlette(
        routes=[Route("/file.txt", lambda _r: PlainTextResponse("fallback"))]
    )
    app.add_middleware(PublicStaticMiddleware, public_dir=public_dir)

    def mock_is_file(_self: Path) -> bool:
        raise OSError("Disk failure")

    monkeypatch.setattr(Path, "is_file", mock_is_file)
    client = TestClient(app)

    # Act
    res = client.get("/file.txt")

    # Assert
    assert res.status_code == 200
    assert res.text == "fallback"
