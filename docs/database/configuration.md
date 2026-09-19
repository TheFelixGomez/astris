# Database Configuration

Astris provides an out-of-the-box database layer powered by **SQLModel**, **SQLAlchemy 2.0**, and **Alembic**.

## Connection Strings & Database Drivers (`DATABASE_URL`)

Set your database connection URL in your project's `.env` file:

### SQLite (Default for Local Development)
Built into Python with zero dependencies required:
```ini
DATABASE_URL=sqlite:///database/app.db
```

### PostgreSQL
Requires the `psycopg2-binary` driver:
```bash
uv add psycopg2-binary
```

Connection URL:
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/my_database
```

### MySQL / MariaDB
Requires the `pymysql` driver:
```bash
uv add pymysql
```

Connection URL:
```ini
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/my_database
```

## Driver Diagnostics

If a required driver is missing when your application starts, Astris catches the error and provides an immediate, actionable installation hint:

```text
RuntimeError: Missing database driver 'psycopg2' for postgresql database.
To resolve, run:
  uv add psycopg2-binary
```

## Automatic Table Creation (`AUTO_CREATE_TABLES`)

Astris manages table creation based on your environment:

* **Local Development (`APP_ENV=local`)**: Defaults to `True`. All tables defined in `app/modules/*/*_model.py` are automatically created on startup for instant development velocity.
* **Production (`APP_ENV=production`)**: Defaults to `False`. Automatic table creation is disabled to prevent accidental schema changes. Use `uv run orbit migrate` to apply versioned migrations.

You can explicitly override this behavior in `.env`:

```ini
AUTO_CREATE_TABLES=false
```

## Engine Configuration

The database engine is configured automatically by the `Astris` kernel on startup via `astris.database.db`.

You can configure query logging in `.env`:

```ini
# Print raw SQL queries to console
DB_ECHO=true
```

## Next Steps

* Define tables and models: [SQLModel Models](/database/models).
* Execute queries and transactions: [Queries & CRUD](/database/queries).
* Run schema migrations: [Alembic Migrations](/database/migrations).
