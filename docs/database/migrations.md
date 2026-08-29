# Schema Migrations

Astris uses **Alembic** under the hood, with seamless integration managed by the **Orbit CLI**.

## Automatic Migration Setup

When you create a project, Astris automatically initializes Alembic and sets up:
* `alembic.ini`: Migration configuration.
* `database/migrations/env.py`: Auto-configured migration environment.
* `database/migrations/versions/`: Directory containing revision scripts.

## Running Migrations (`orbit migrate`)

To apply all pending database migrations:

```bash
uv run orbit migrate
```

## Creating Migrations (`orbit make:migration`)

When you create or update a SQLModel table, generate an auto-detected migration revision with:

```bash
uv run orbit make:migration "create articles table"
```

Alembic will inspect your SQLModel models, compare them to the current database state, and generate a new version file in `database/migrations/versions/`.

::: info Powered by Alembic
Because Astris generates standard Alembic revision files, all advanced migration features (such as data migrations, custom downgrade logic, and manual schema operations) are fully supported.

Visit the [official Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/) to learn more about advanced migration capabilities.
:::

## Next Steps

* Add authentication: [Authentication Starter Kit](/security/authentication).
* Secure routes with guards: [Auth Guards & Dependencies](/security/guards).
