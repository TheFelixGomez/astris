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
   * `auth_model.py`: `User` SQLModel table, registration/login schemas, and profile/password update schemas.
   * `auth_service.py`: Authentication, registration, profile update, and password change logic.
   * `auth_controller.py`: Endpoints for `/login`, `/register`, `/logout`, `/profile`, `/password`, and `/dashboard`.
2. **Backend Tasks Module (`app/modules/tasks/`)**:
   * `task_model.py`: `Task` SQLModel table with foreign key relationship to `User`.
   * `task_service.py`: Complete task CRUD operations (list, create, toggle completion, delete).
   * `task_controller.py`: RESTful endpoints for creating, toggling, and deleting tasks.
3. **Database Migration (`database/migrations/versions/`)**:
   * `0001_initial_schema.py`: Pre-generated initial Alembic migration creating both `user` and `task` tables.
4. **Frontend Vue 3 Views (`resources/js/Pages/`)**:
   * `Pages/Auth/Login.vue`: Complete login form with error handling and remember-me checkbox.
   * `Pages/Auth/Register.vue`: Full user registration flow.
   * `Pages/Dashboard.vue`: Interactive user dashboard with 3 tabs: Tasks CRUD (live Inertia `useForm`, status toggles, deletion), Profile & Security (update profile info and password), and System Info.

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
