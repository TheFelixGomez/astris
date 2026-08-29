# Authentication Starter Kit

Astris includes a full-stack authentication system out of the box with zero boilerplate.

## Installing Authentication

### Included by Default
Authentication is pre-installed automatically when creating any new project:
```bash
uvx --from astris-python astris new my_app
```

### Adding to an Existing Project
If you created a project with `--no-auth` and later want to add authentication:
```bash
uv run orbit make:auth
```

## What the Auth Starter Includes

Running `make:auth` scaffolds:

1. **Backend Auth Module (`app/modules/auth/`)**:
   * `auth_model.py`: `User` SQLModel table with Argon2id password hashing.
   * `auth_service.py`: `AuthService.authenticate()` and `register()`.
   * `auth_controller.py`: Endpoints for `/login`, `/register`, `/logout`, and `/dashboard`.
2. **Frontend Vue 3 Views (`resources/js/Pages/Auth/`)**:
   * `Login.vue`: Complete login form with error handling and remember-me checkbox.
   * `Register.vue`: Full user registration flow.
   * `Dashboard.vue`: Authenticated user area with session state.

## Argon2id Password Hashing (`pwdlib`)

Astris uses **Argon2id** (the OWASP recommended password hashing algorithm) via `pwdlib`:

```python
from astris.auth import hash_password, verify_and_update_password

# Hash password
hashed = hash_password("supersecret123")

# Verify password (and check if rehash is needed)
is_valid, new_hash = verify_and_update_password("supersecret123", hashed)
```

## Next Steps

* Guard your routes: [Auth Guards & Dependencies](/security/guards).
* Understand CSRF protection: [CSRF Protection](/security/csrf).
