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

## Scaffolding Models with Orbit

To generate a new database model via the CLI:

```bash
uv run orbit make:model Article
```

## Next Steps

* Query and update records: [Queries & CRUD](/database/queries).
* Generate database migrations: [Schema Migrations](/database/migrations).
