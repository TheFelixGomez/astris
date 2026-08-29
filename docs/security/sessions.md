# Signed Cookie Sessions

Astris uses cryptographically signed and encrypted HTTP cookies for tamper-proof session persistence.

## How Sessions Work

Unlike traditional database sessions that require querying a session store on every HTTP hit, Astris signs session payloads using the secret **`APP_KEY`** via `SessionMiddleware`.

This guarantees:
* **Stateless Performance**: Zero extra database latency on requests.
* **Tamper Proofing**: Any client modification invalidates the signature and clears the session.
* **Secure Cookie Attributes**: Configured with `HttpOnly` and `SameSite=Lax`.

## Session Configuration

Configure session cookies in `.env`:

```ini
APP_KEY=your_32_byte_secret_key
SESSION_COOKIE_NAME=astris_session
SESSION_MAX_AGE=1209600
SESSION_HTTPS_ONLY=false
```

## Using Sessions in Python

Access and mutate the session dictionary via `request.session`:

```python
from astris.routing import Controller
from astris.http import Request

controller = Controller(prefix="/auth")


@controller.post("/login")
async def login(request: Request):
    # Store session data
    request.session["user_id"] = 1
    request.session["logged_in"] = True
    return {"status": "ok"}


@controller.post("/logout")
async def logout(request: Request):
    # Clear session data
    request.session.clear()
    return {"status": "logged_out"}
```

## Next Steps

* CLI reference: [Orbit CLI Reference](/cli/orbit).
* Deploying to production: [Production & Docker](/deployment/production).
