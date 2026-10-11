from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, WebSocketRoute
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from astris.security.csrf import CSRFMiddleware


def test_csrf_middleware_behavior():
    # Arrange
    async def get_page(request: Request) -> PlainTextResponse:
        _ = request
        return PlainTextResponse("Hello")

    async def post_action(request: Request) -> JSONResponse:
        _ = request
        return JSONResponse({"status": "ok"})

    async def webhook(request: Request) -> JSONResponse:
        _ = request
        return JSONResponse({"webhook": "received"})

    async def ws_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_text("ws-ok")
        await websocket.close()

    app = Starlette(
        routes=[
            Route("/", get_page, methods=["GET"]),
            Route("/submit", post_action, methods=["POST", "PUT", "PATCH", "DELETE"]),
            Route("/api/webhook", webhook, methods=["POST"]),
            WebSocketRoute("/ws", ws_endpoint),
        ]
    )
    app.add_middleware(
        CSRFMiddleware,
        cookie_name="XSRF-TOKEN",
        cookie_path="/",
        cookie_domain="example.com",
        cookie_secure=True,
        cookie_samesite="strict",
        exempt_paths=["/api/webhook"],
    )
    client = TestClient(app, base_url="https://example.com")

    # Act & Assert 1: Non-http scope (websocket) passes through
    with client.websocket_connect("/ws") as ws:
        text = ws.receive_text()
        assert text == "ws-ok"

    # Act & Assert 2: Initial GET request generates XSRF-TOKEN cookie
    res_get = client.get("/")
    assert res_get.status_code == 200
    assert "XSRF-TOKEN" in res_get.cookies
    token = res_get.cookies["XSRF-TOKEN"]
    assert "Secure" in res_get.headers.get("set-cookie", "")
    assert "Domain=example.com" in res_get.headers.get("set-cookie", "")
    assert "SameSite=Strict" in res_get.headers.get("set-cookie", "")

    # Act & Assert 3: Subsequent GET with existing cookie preserves it
    res_get2 = client.get("/")
    assert res_get2.status_code == 200
    assert "set-cookie" not in res_get2.headers

    # Act & Assert 4: POST with matching header x-xsrf-token succeeds
    res_post_ok = client.post(
        "/submit",
        headers={"x-xsrf-token": token},
    )
    assert res_post_ok.status_code == 200
    assert res_post_ok.json() == {"status": "ok"}

    # Act & Assert 5: POST with matching header x-csrf-token succeeds
    res_post_csrf = client.post(
        "/submit",
        headers={"x-csrf-token": token},
    )
    assert res_post_csrf.status_code == 200

    # Act & Assert 6: POST missing header returns 419
    res_no_header = client.post("/submit")
    assert res_no_header.status_code == 419
    assert res_no_header.json() == {"message": "CSRF token mismatch or missing."}

    # Act & Assert 7: POST with mismatched tokens returns 419
    res_mismatch = client.post(
        "/submit",
        headers={"x-xsrf-token": "wrong-token"},
    )
    assert res_mismatch.status_code == 419

    # Act & Assert 8: POST without cookie or header returns 419
    fresh_client = TestClient(app, base_url="https://example.com")
    res_no_cookie = fresh_client.post("/submit", headers={"x-xsrf-token": token})
    assert res_no_cookie.status_code == 419

    # Act & Assert 9: Exempt path succeeds even without tokens
    res_exempt = client.post("/api/webhook")
    assert res_exempt.status_code == 200
    assert res_exempt.json() == {"webhook": "received"}
