import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.types import Message, Receive, Scope, Send

from astris.inertia.exceptions import (
    inertia_http_exception_handler,
    inertia_validation_exception_handler,
)
from astris.inertia.response import InertiaResponse
from astris.inertia.shared import (
    FlashMiddleware,
    flash,
    resolve_shared_props,
    share,
)
from astris.inertia.vite import get_vite_tags, is_vite_running


class PropModel(BaseModel):
    title: str
    count: int


def test_inertia_response_lifecycle(tmp_path: Path):
    # Arrange
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    views_dir = tmp_path / "resources" / "views"
    views_dir.mkdir(parents=True, exist_ok=True)
    root_html = views_dir / "root.html"
    root_html.write_text("<html><head>@vite</head><body>@inertia</body></html>")

    @app.get("/inertia-test")
    def inertia_endpoint(request: Request):
        return InertiaResponse(
            request=request,
            component="Test/Index",
            props={
                "name": "Astris",
                "model": PropModel(title="Test", count=5),
                "created_at": datetime(2026, 9, 18, 12, 0, 0, tzinfo=UTC),
            },
            root_template=str(root_html),
            headers={"X-Custom-Header": "custom-val"},
        )

    @app.get("/fallback-template")
    def fallback_endpoint(request: Request):
        return InertiaResponse(
            request=request,
            component="Test/Fallback",
            props={},
            root_template="non_existent/root.html",
        )

    client = TestClient(app)

    # Act
    res_html = client.get("/inertia-test")
    res_json = client.get("/inertia-test", headers={"X-Inertia": "true"})
    res_fallback = client.get("/fallback-template")
    client.cookies.set("_inertia_flash", "flash")
    client.cookies.set("_inertia_errors", "err")
    res_cleanup = client.get(
        "/inertia-test",
        headers={"X-Inertia": "true"},
    )

    # Assert
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert '<div id="app" data-page="' in res_html.text
    assert "X-Custom-Header" in res_html.headers

    assert res_json.status_code == 200
    assert res_json.headers["x-inertia"] == "true"
    assert "X-Inertia" in res_json.headers["vary"]
    data = res_json.json()
    assert data["component"] == "Test/Index"
    assert data["props"]["name"] == "Astris"
    assert data["props"]["model"] == {"title": "Test", "count": 5}
    assert "2026-09-18T12:00:00" in data["props"]["created_at"]

    assert res_fallback.status_code == 200
    assert "<!DOCTYPE html>" in res_fallback.text

    assert res_cleanup.status_code == 200


def test_shared_props_and_flash():
    # Arrange
    share("app_title", "Astris Test")
    share({"version": "1.0", "env": "testing"})
    share(lambda _req: {"calc": 42})

    async def async_factory(_req: Request) -> dict[str, str]:
        return {"async_val": "loaded"}

    share(async_factory)

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    app.add_middleware(FlashMiddleware)

    @app.get("/flash-action")
    def flash_action(request: Request) -> dict[str, bool]:
        flash(request, "success", "Item created!")
        return {"flashed": True}

    @app.get("/resolve-test")
    async def resolve_test(request: Request) -> dict[str, object]:
        props = await resolve_shared_props(request)
        return props

    @app.get("/flash-response")
    def flash_resp(request: Request) -> JSONResponse:
        _ = request
        resp = JSONResponse({"ok": True})
        flash(resp, "warning", "Warning message")
        return resp

    client = TestClient(app)

    # Act
    client.get("/flash-action")
    res = client.get("/resolve-test")
    res_resp = client.get("/flash-response")
    props = res.json()

    # Assert
    assert props["app_title"] == "Astris Test"
    assert props["version"] == "1.0"
    assert props["calc"] == 42
    assert props["async_val"] == "loaded"
    assert props["flash"].get("success") == "Item created!"
    assert "_inertia_flash" in res_resp.cookies


def test_vite_tags(tmp_path: Path):
    # Arrange
    public_dir = tmp_path / "public"
    public_dir.mkdir()
    hot_file = public_dir / "hot"
    hot_file.write_text("http://127.0.0.1:5173\n")

    # Act & Assert 1: Non running socket
    assert is_vite_running("http://127.0.0.1:59999", timeout=0.01) is False

    # Act & Assert 2: Hot file detection
    tags_fallback = get_vite_tags(base_path=tmp_path)
    assert "/@vite/client" in tags_fallback

    # Act & Assert 3: Production manifest detection
    build_dir = public_dir / "build" / ".vite"
    build_dir.mkdir(parents=True)
    manifest = build_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "resources/js/app.ts": {
                    "file": "assets/app-abc.js",
                    "css": ["assets/app-xyz.css"],
                    "isEntry": True,
                }
            }
        )
    )

    hot_file.unlink()
    tags_prod = get_vite_tags(base_path=tmp_path)
    assert '<link rel="stylesheet" href="/build/assets/app-xyz.css">' in tags_prod
    assert '<script type="module" src="/build/assets/app-abc.js">' in tags_prod


def test_validation_exceptions_handling():
    # Arrange
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    app.add_exception_handler(
        RequestValidationError, inertia_validation_exception_handler
    )
    app.add_exception_handler(ValidationError, inertia_validation_exception_handler)
    app.add_exception_handler(HTTPException, inertia_http_exception_handler)

    class ItemPayload(BaseModel):
        name: str
        age: int

    @app.post("/items")
    def create_item(payload: ItemPayload):
        return {"name": payload.name}

    @app.get("/error-422")
    def trigger_422():
        raise HTTPException(status_code=422, detail={"field": "Custom 422 error"})

    @app.get("/error-500")
    def trigger_500():
        raise HTTPException(status_code=500, detail="Internal Error")

    client = TestClient(app)

    # Act
    res_api = client.post("/items", json={"name": "Alice", "age": "not-an-int"})
    res_inertia_redir = client.post(
        "/items",
        json={"name": "Alice", "age": "invalid"},
        headers={"X-Inertia": "true", "Referer": "http://testserver/form"},
        follow_redirects=False,
    )
    res_inertia_no_ref = client.post(
        "/items",
        json={},
        headers={"X-Inertia": "true"},
    )
    res_http_422 = client.get("/error-422", headers={"X-Inertia": "true"})
    res_http_500 = client.get("/error-500")

    # Assert
    assert res_api.status_code == 422
    assert "detail" in res_api.json()
    assert "errors" in res_api.json()

    assert res_inertia_redir.status_code == 303
    assert res_inertia_redir.headers["location"] == "http://testserver/form"
    assert "_inertia_errors" in res_inertia_redir.cookies

    assert res_inertia_no_ref.status_code == 422
    assert res_inertia_no_ref.headers["x-inertia"] == "true"
    assert "errors" in res_inertia_no_ref.json()

    assert res_http_422.status_code == 422
    assert res_http_422.headers["x-inertia"] == "true"

    assert res_http_500.status_code == 500
    assert res_http_500.json() == {"detail": "Internal Error"}


@pytest.mark.anyio
async def test_flash_middleware_and_shared_props_branches():
    # Arrange 1: FlashMiddleware non-http scope
    dummy_app_called = False

    async def dummy_app(scope: Scope, receive: Receive, send: Send) -> None:
        _ = (scope, receive, send)
        nonlocal dummy_app_called
        dummy_app_called = True

    async def dummy_receive() -> Message:
        return {"type": "http.request"}

    async def dummy_send(message: Message) -> None:
        pass

    mw = FlashMiddleware(dummy_app)

    # Act 1
    await mw({"type": "websocket"}, dummy_receive, dummy_send)

    # Assert 1
    assert dummy_app_called is True

    # Arrange 2: FlashMiddleware without session persists flashes via cookie header
    messages_sent: list[Message] = []

    async def inner_app(scope: Scope, receive: Receive, send: Send) -> None:
        _ = receive
        request = Request(scope)
        request.state.flash_messages = {"saved": "true"}
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def mock_send(msg: Message) -> None:
        messages_sent.append(msg)

    mw2 = FlashMiddleware(inner_app)

    # Act 2
    await mw2(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
        },
        dummy_receive,
        mock_send,
    )

    # Assert 2
    start_msg = messages_sent[0]
    headers_dict = dict(start_msg["headers"])
    assert b"set-cookie" in headers_dict
    assert b"_inertia_flash=" in headers_dict[b"set-cookie"]

    # Arrange 3: Shared props resolution
    share("sync_key", lambda _req: "sync_value")

    async def async_key_fn(_req: Request) -> str:
        return "async_value"

    share("async_key", async_key_fn)

    flash_payload = quote(json.dumps({"cookie_flash": "msg"}))
    err_payload = quote(json.dumps({"cookie_err": "bad"}))
    raw_cookies = f"_inertia_flash={flash_payload}; _inertia_errors={err_payload}"

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"cookie", raw_cookies.encode())],
        "session": {
            "user_id": 999,
            "_flash": {"session_flash": "ok"},
            "_errors": {"session_err": "oops"},
        },
    }
    req = Request(scope)
    req.state.inertia_shared_props = {"from_state": 123}
    req.state.flash_messages = {"state_flash": "yes"}
    req.state.errors = {"state_err": "nope"}

    scope_corrupt = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (b"cookie", b"_inertia_flash={bad-json; _inertia_errors={bad-json")
        ],
    }
    req_corrupt = Request(scope_corrupt)

    # Act 3
    resolved = await resolve_shared_props(req)
    resolved_corrupt = await resolve_shared_props(req_corrupt)

    # Assert 3
    assert resolved["auth"]["user"] == {"id": 999}
    assert resolved["from_state"] == 123
    assert resolved["sync_key"] == "sync_value"
    assert resolved["async_key"] == "async_value"
    assert resolved["flash"]["state_flash"] == "yes"
    assert resolved["flash"]["session_flash"] == "ok"
    assert resolved["flash"]["cookie_flash"] == "msg"
    assert resolved["errors"]["state_err"] == "nope"
    assert resolved["errors"]["session_err"] == "oops"
    assert resolved["errors"]["cookie_err"] == "bad"

    assert resolved_corrupt["flash"] == {}
    assert resolved_corrupt["errors"] == {}


def test_vite_tags_more_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    import socket
    from unittest.mock import MagicMock

    mock_sock = MagicMock()
    mock_sock.__enter__.return_value = mock_sock
    monkeypatch.setattr(
        socket, "create_connection", lambda *_args, **_kwargs: mock_sock
    )

    # Act & Assert 1: is_vite_running returns True via mocked socket
    assert is_vite_running("http://localhost:5173") is True

    # Act & Assert 2: get_vite_tags when Vite is running
    tags_dev = get_vite_tags(entry="/resources/js/app.ts", base_path=tmp_path)
    assert "<!-- Vite Dev Server Scripts -->" in tags_dev
    assert (
        '<script type="module" src="http://localhost:5173/resources/js/app.ts"></script>'
        in tags_dev
    )

    # Act & Assert 3: get_vite_tags with corrupted manifest falls back to dev tags
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError),
    )
    public_build = tmp_path / "public" / "build"
    public_build.mkdir(parents=True, exist_ok=True)
    bad_manifest = public_build / "manifest.json"
    bad_manifest.write_text("invalid json", encoding="utf-8")
    tags_corrupt = get_vite_tags(base_path=tmp_path)
    assert "<!-- Vite Assets (Fallback) -->" in tags_corrupt

    # Act & Assert 4: manifest entry lookup by src match
    manifest_by_src = {
        "arbitrary_key": {
            "src": "resources/js/app.ts",
            "file": "assets/app-src.js",
            "css": ["assets/app-src.css"],
        }
    }
    bad_manifest.write_text(json.dumps(manifest_by_src), encoding="utf-8")
    tags_by_src = get_vite_tags(entry="resources/js/app.ts", base_path=tmp_path)
    assert (
        '<script type="module" src="/build/assets/app-src.js"></script>' in tags_by_src
    )

    # Act & Assert 5: manifest entry lookup by endsWith match
    manifest_by_suffix = {
        "deeply/nested/resources/js/app.ts": {
            "file": "assets/app-suffix.js",
            "css": [],
        }
    }
    bad_manifest.write_text(json.dumps(manifest_by_suffix), encoding="utf-8")
    tags_by_suffix = get_vite_tags(entry="resources/js/app.ts", base_path=tmp_path)
    assert (
        '<script type="module" src="/build/assets/app-suffix.js"></script>'
        in tags_by_suffix
    )


@pytest.mark.anyio
async def test_exception_handler_detail_types():
    # Arrange
    req_inertia = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [(b"x-inertia", b"true")],
        }
    )
    req_api = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
        }
    )
    exc_list_dict = HTTPException(
        status_code=422, detail=[{"loc": ["body", "email"], "msg": "Invalid format"}]
    )
    exc_list_str = HTTPException(status_code=422, detail=["Simple error in list"])
    exc_str = HTTPException(status_code=422, detail="String error")
    exc_int = HTTPException(status_code=422, detail=123)

    # Act
    res_val_generic = await inertia_validation_exception_handler(
        req_inertia, Exception("generic failure")
    )
    res_val_api = await inertia_validation_exception_handler(
        req_api, Exception("generic failure")
    )
    res_list_dict = await inertia_http_exception_handler(req_inertia, exc_list_dict)
    res_list_str = await inertia_http_exception_handler(req_inertia, exc_list_str)
    res_str = await inertia_http_exception_handler(req_inertia, exc_str)
    res_int = await inertia_http_exception_handler(req_inertia, exc_int)

    # Assert
    assert res_val_generic.status_code == 422
    assert res_val_generic.headers["x-inertia"] == "true"

    assert res_val_api.status_code == 422

    assert res_list_dict.status_code == 422
    assert json.loads(bytes(res_list_dict.body))["errors"] == {
        "email": "Invalid format"
    }

    assert res_list_str.status_code == 422
    assert json.loads(bytes(res_list_str.body))["errors"] == {
        "non_field_errors": "Simple error in list"
    }

    assert res_str.status_code == 422
    assert json.loads(bytes(res_str.body))["errors"] == {
        "non_field_errors": "String error"
    }

    assert res_int.status_code == 422
    assert json.loads(bytes(res_int.body))["errors"] == {
        "non_field_errors": "Validation error"
    }
