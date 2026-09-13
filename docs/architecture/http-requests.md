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

::: details Inspecting the `Request` object

* **Client IP (`request.client.host`)**:
  ```python
  client_ip = request.client.host if request.client else "unknown"
  ```
  Retrieves the client's remote IP address. Checking `if request.client` ensures your code doesn't crash if the request was initiated without socket metadata.
* **HTTP Headers (`request.headers`)**:
  ```python
  user_agent = request.headers.get("user-agent")
  ```
  Reads incoming headers case-insensitively (`"User-Agent"` and `"user-agent"` match identically).
* **Encrypted Sessions (`request.session`)**:
  ```python
  user_id = request.session.get("user_id")
  ```
  Reads decrypted session data. Astris's `SessionMiddleware` automatically decrypts and verifies the browser's signed cookie using your `APP_KEY`.
* **Request State (`request.state`)**:
  ```python
  user = getattr(request.state, "user", None)
  ```
  Accesses arbitrary data attached to the request lifecycle by custom middleware or authentication guards.

:::

## Response Types

### 1. Redirects (`RedirectResponse`)

When redirecting after a form submission or database mutation in Inertia, always use a `303 See Other` status code:

```python
from astris.http import RedirectResponse, status
from astris.inertia import flash

@controller.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    flash(request, "info", "You have been logged out successfully.")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
```

::: details Why HTTP 303 is required for Inertia

In single-page applications, browsers follow `302` or `307` redirects by repeating the original HTTP method (`POST`). Returning `status.HTTP_303_SEE_OTHER` instructs the browser and Inertia client to switch to an HTTP `GET` request when loading the target page (`/login`), preventing duplicate form submissions.

:::

### 2. JSON Responses (`JSONResponse` / Dictionaries)

Astris automatically serializes Python dictionaries, lists, and Pydantic/SQLModel models into JSON:

```python
@controller.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": "2026-08-28T12:00:00Z"}
```

Astris automatically sets the `Content-Type: application/json` header and formats the payload according to OpenAPI standards.

### 3. File Downloads (`FileResponse`)

Stream files directly from your disk to the client:

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

::: details Parameter breakdown

* **`path=file_path`**: The absolute or relative filesystem path to the file.
* **`filename="..."`**: Sets the `Content-Disposition: attachment; filename="..."` header, prompting the user's browser to download the file with that name.
* **`media_type="application/pdf"`**: Specifies the exact MIME type.

:::

### 4. Background Tasks (`BackgroundTasks`)

Execute asynchronous tasks after returning an immediate response to the user:

```python
from astris.http import BackgroundTasks

def send_welcome_email(email: str):
    # Perform slow network or email operations here
    pass

@controller.post("/signup")
async def signup(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_welcome_email, email)
    return {"status": "Registration successful. Email queued."}
```

::: details How background tasks work

1. **`background_tasks: BackgroundTasks`**: Astris automatically provides a task manager dependency.
2. **`background_tasks.add_task(func, *args, **kwargs)`**: Enqueues the function call.
3. **Immediate response**: The HTTP response is returned to the user instantly with zero perceived latency.
4. **Execution**: Once the response is sent, the ASGI worker executes `send_welcome_email(email)` in the background.

:::

## Next Steps

* Learn how Astris auto-discovers your code: [Module Auto-Discovery](/architecture/module-discovery).
* Dive into frontend rendering: [Inertia.js Overview](/frontend/inertia).
