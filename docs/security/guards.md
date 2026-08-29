# Auth Guards & Dependencies

Astris provides intuitive dependencies for protecting routes and retrieving the current user.

## Available Auth Dependencies

```python
from astris.auth import AuthUser, auth_required, guest_only
```

## 1. Requiring Authentication (`auth_required`)

To protect an entire controller or a single route:

### Protecting a Controller:
```python
from astris.routing import Controller
from astris.auth import auth_required, AuthUser
from astris.http import Request
from astris.inertia import InertiaResponse

# All routes in this controller require an authenticated user
controller = Controller(prefix="/settings", dependencies=[auth_required])


@controller.get("/")
async def settings_page(request: Request, user: AuthUser) -> InertiaResponse:
    # Unauthenticated requests are automatically redirected to /login
    return InertiaResponse(request, "Settings/Index", props={"user": user})
```

## 2. Guest-Only Routes (`guest_only`)

For pages that should only be viewed by unauthenticated guests (like `/login` or `/register`):

```python
from astris.auth import guest_only

@controller.get("/login", dependencies=[guest_only])
async def login_page(request: Request) -> InertiaResponse:
    # Authenticated users are automatically redirected to /dashboard
    return InertiaResponse(request, "Auth/Login")
```

## 3. Injecting the Current User (`AuthUser`)

When a route is protected, inject `user: AuthUser` to get the authenticated user's dictionary/model:

```python
@controller.get("/api/me")
async def current_user(user: AuthUser):
    return {"id": user["id"], "email": user["email"], "name": user["name"]}
```

## Next Steps

* Learn about CSRF defense: [CSRF Protection](/security/csrf).
* Configure signed sessions: [Signed Cookie Sessions](/security/sessions).
