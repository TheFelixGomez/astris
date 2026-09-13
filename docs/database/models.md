# SQLModel Models

Astris uses **SQLModel**, combining the power of **SQLAlchemy** with the validation and typing of **Pydantic**.

## Defining a Model

In Astris, database models typically live alongside their domain controller in `app/modules/<module>/<module>_model.py`:

```python
from astris.database import SQLModel, Field


# 1. Base schema (shared fields for validation & DTOs)
class ArticleBase(SQLModel):
    title: str = Field(index=True, min_length=3, max_length=150)
    content: str
    is_published: bool = Field(default=False)


# 2. Database table definition
class Article(ArticleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


# 3. Create request schema
class ArticleCreate(ArticleBase):
    pass


# 4. Update request schema
class ArticleUpdate(SQLModel):
    title: str | None = None
    content: str | None = None
    is_published: bool | None = None
```

::: details Step-by-step model breakdown

### Step 1: Define shared fields in `ArticleBase`

```python
class ArticleBase(SQLModel):
    title: str = Field(index=True, min_length=3, max_length=150)
    content: str
    is_published: bool = Field(default=False)
```

* Defines common fields shared across database records and API requests without duplicating code.
* `index=True`: Instructs SQLAlchemy and Alembic to create a database index on `title` for high-speed lookups.
* `min_length=3, max_length=150`: Pydantic validation rules applied whenever data is deserialized.

### Step 2: Define the database table in `Article`

```python
class Article(ArticleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

* `table=True`: Tells SQLModel and SQLAlchemy that this class represents a real table in your database.
* Inherits all fields (`title`, `content`, `is_published`) from `ArticleBase`.
* `id: int | None = Field(default=None, primary_key=True)`: Declares the primary key. Defaults to `None` so you can instantiate models in Python before the database generates the auto-increment ID.

### Step 3: Create the creation schema in `ArticleCreate`

```python
class ArticleCreate(ArticleBase):
    pass
```

Inherits all base fields for `POST` requests, but safely omits `id` so clients cannot overwrite primary keys.

### Step 4: Create the update schema in `ArticleUpdate`

```python
class ArticleUpdate(SQLModel):
    title: str | None = None
    content: str | None = None
    is_published: bool | None = None
```

All fields default to `None`. This allows clients to perform partial updates (`PUT`/`PATCH`) without sending the entire object.

:::

## Scaffolding Models with Orbit

To generate a new database model via the CLI:

```bash
uv run orbit make:model Article
```

Creates `app/modules/article/article_model.py` with standard schemas pre-configured.

## Next Steps

* Query and update records: [Queries & CRUD](/database/queries).
* Generate database migrations: [Schema Migrations](/database/migrations).
