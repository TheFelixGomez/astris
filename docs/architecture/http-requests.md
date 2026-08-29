# HTTP Requests & Responses

Astris re-exports all standard HTTP abstractions from `astris.http` so you can handle requests and return responses with zero extra imports.

## Available Imports

```python
from astris.http import (
    Request,
    Response,
    RedirectResponse,
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    FileResponse,
    StreamingResponse,
    BackgroundTasks,
    HTTPException,
    status,
)
```

## Working with `Request`

The `Request` object represents the incoming HTTP request:

```python
from astris.routing import Controller
from astris.http import Request

controller = Controller(prefix="/profile")


@controller.get("/")
async def get_profile(request: Request):
    # Client IP and Headers
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    # Access session data
    user_id = request.session.get("user_id")

    # Access request state
    user = getattr(request.state, "user", None)

    return {"ip": client_ip, "user_agent": user_agent, "user_id": user_id}
```

## Response Types

### 1. Redirects (`RedirectResponse`)
When redirecting after a form submission in Inertia, use a `303 See Other` status code:

```python
from astris.http import RedirectResponse, status

@controller.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
```

### 2. JSON Responses (`JSONResponse` / Dictionaries)
FastAPI and Astris automatically serialize Python dictionaries, lists, and Pydantic/SQLModel models into JSON:

```python
@controller.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": "2026-08-28T12:00:00Z"}
```

### 3. File Downloads (`FileResponse`)
```python
from pathlib import Path
from astris.http import FileResponse

@controller.get("/invoices/{invoice_id}/pdf")
async def download_invoice(invoice_id: int):
    file_path = Path("storage/invoices") / f"{invoice_id}.pdf"
    return FileResponse(
        path=file_path,
        filename=f"invoice-{invoice_id}.pdf",
        media_type="application/pdf",
    )
```

### 4. Background Tasks (`BackgroundTasks`)
Execute asynchronous tasks after returning a response:

```python
from astris.http import BackgroundTasks

def send_welcome_email(email: str):
    # Send email logic here
    pass

@controller.post("/signup")
async def signup(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_welcome_email, email)
    return {"status": "Registration successful. Email queued."}
```

## Next Steps

* Learn how Astris auto-discovers your code: [Module Auto-Discovery](/architecture/module-discovery).
* Dive into frontend rendering: [Inertia.js Overview](/frontend/inertia).
