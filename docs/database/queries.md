# Queries & CRUD

Astris provides database session management and query helpers through `astris.database` and `sqlmodel`.

## Executing CRUD Operations (`DatabaseSession`)

In controllers and route handlers, inject the `DatabaseSession` dependency. Astris automatically manages the session lifecycle, committing or rolling back per request:

```python
from astris.routing import Controller
from astris.http import Request, RedirectResponse, status
from astris.inertia import InertiaResponse, flash
from astris.database import DatabaseSession, select
from app.modules.articles.articles_model import Article, ArticleCreate, ArticleUpdate

controller = Controller(prefix="/articles")


# 1. Read (Select)
@controller.get("/")
async def index(request: Request, session: DatabaseSession) -> InertiaResponse:
    statement = select(Article).where(Article.is_published == True)
    articles = session.exec(statement).all()
    article_data = [article.model_dump() for article in articles]

    return InertiaResponse(request, "Articles/Index", props={"articles": article_data})


# 2. Read Single Record
@controller.get("/{article_id}")
async def show(request: Request, article_id: int, session: DatabaseSession) -> InertiaResponse:
    article = session.get(Article, article_id)
    return InertiaResponse(request, "Articles/Show", props={"article": article.model_dump()})


# 3. Create (Insert)
@controller.post("/")
async def store(request: Request, dto: ArticleCreate, session: DatabaseSession) -> RedirectResponse:
    article = Article.model_validate(dto)
    session.add(article)
    session.commit()
    session.refresh(article)
    flash(request, "success", "Article created successfully!")
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)


# 4. Update
@controller.put("/{article_id}")
async def update(article_id: int, dto: ArticleUpdate, session: DatabaseSession, request: Request) -> RedirectResponse:
    article = session.get(Article, article_id)
    if article:
        article.sqlmodel_update(dto.model_dump(exclude_unset=True))
        session.add(article)
        session.commit()
        session.refresh(article)
        flash(request, "success", "Article updated!")
    return RedirectResponse(url=f"/articles/{article_id}", status_code=status.HTTP_303_SEE_OTHER)


# 5. Delete
@controller.delete("/{article_id}")
async def destroy(article_id: int, session: DatabaseSession, request: Request) -> RedirectResponse:
    article = session.get(Article, article_id)
    if article:
        session.delete(article)
        session.commit()
        flash(request, "info", "Article deleted.")
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)
```

::: details Step-by-step CRUD operations breakdown

#### 1. Querying Multiple Records (`select`)
* **`session: DatabaseSession`**: Injects an active database session managed by Astris's dependency injection system. The connection is acquired from the engine pool and safely closed when the request finishes.
* **`statement = select(Article).where(Article.is_published == True)`**: Prepares a SQL `SELECT` statement. Type hints ensure that column attributes like `Article.is_published` are validated by your IDE and linter.
* **`session.exec(statement).all()`**: Executes the SQL query against your database engine and returns a list of `Article` model instances.
* **`[article.model_dump() for article in articles]`**: Serializes the SQLModel instances into standard Python dictionaries for clean JSON serialization inside the Inertia payload.

#### 2. Reading a Single Record (`session.get`)
* **`session.get(Article, article_id)`**: Queries the database directly by primary key. If a record exists, it returns the `Article` instance; if not found, it returns `None`.

#### 3. Creating a Record (`session.add`)
* **`article = Article.model_validate(dto)`**: Converts the validated `ArticleCreate` Pydantic schema into a database `Article` model.
* **`session.add(article)`**: Stages the new object in the current transaction unit-of-work.
* **`session.commit()`**: Flushes and commits the transaction to disk, writing the new row into your SQL table.
* **`session.refresh(article)`**: Reloads the instance from the database, populating the auto-generated `id` and any database defaults.

#### 4. Updating a Record (`sqlmodel_update`)
* **`dto.model_dump(exclude_unset=True)`**: Returns a dictionary containing **only** the fields explicitly passed by the client. Fields that were left empty in the request are excluded.
* **`article.sqlmodel_update(...)`**: Modifies the model in-place with the new attributes.
* **`session.commit()`**: Writes the update statement to the database.

#### 5. Deleting a Record (`session.delete`)
* **`session.delete(article)`**: Marks the retrieved object for deletion.
* **`session.commit()`**: Executes the `DELETE FROM` SQL query.

:::

## Standalone Scripts & CLI Tasks (`db.session()`)

When writing standalone scripts, seeders, or background tasks outside the HTTP request lifecycle, use the `db.session()` context manager:

```python
from astris.database import db, select
from app.modules.articles.articles_model import Article

# Run queries in CLI tasks or seed scripts
with db.session() as session:
    articles = session.exec(select(Article)).all()
    for article in articles:
        print(article.title)
```

::: details How `db.session()` works

* **`from astris.database import db`**: Imports the central database manager.
* **`with db.session() as session:`**: Opens a contextual database session, yielding an active `Session`. When the `with` block exits, the session is closed automatically, and uncommitted transactions are rolled back if an exception occurred.

:::

## Next Steps

* Manage database schemas: [Schema Migrations](/database/migrations).
* Protect routes with auth: [Authentication Starter Kit](/security/authentication).
