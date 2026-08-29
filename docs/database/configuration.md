# Database Configuration

Astris provides an out-of-the-box database layer powered by **SQLModel**, **SQLAlchemy 2.0**, and **Alembic**.

## Connection Strings (`DATABASE_URL`)

Set your database connection URL in your project's `.env` file:

### SQLite (Default for Local Development)
```ini
DATABASE_URL=sqlite:///database/app.db
```

### PostgreSQL
```ini
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/my_database
```

### MySQL
```ini
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/my_database
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
