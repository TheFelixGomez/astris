# Queries & CRUD

Astris provides database session management and query helpers through `astris.database` and `sqlmodel`.

## Executing CRUD Operations (`DatabaseSession`)

In controllers and route handlers, inject the `DatabaseSession` dependency. Astris automatically manages the session lifecycle, committing or rolling back per request:

```python
from astris.routing import Controller
from astris.http import Request
from astris.inertia import InertiaResponse
from astris.database import DatabaseSession, select
from app.modules.articles.articles_model import Article

controller = Controller(prefix="/articles")


# 1. Read (Select)
@controller.get("/")
async def index(request: Request, session: DatabaseSession) -> InertiaResponse:
    # Filtered query
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
async def store(dto: ArticleCreateDTO, session: DatabaseSession):
    article = Article.model_validate(dto)
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


# 4. Update
@controller.put("/{article_id}")
async def update(article_id: int, dto: ArticleUpdateDTO, session: DatabaseSession):
    article = session.get(Article, article_id)
    if article:
        article.sqlmodel_update(dto.model_dump(exclude_unset=True))
        session.add(article)
        session.commit()
        session.refresh(article)
    return article


# 5. Delete
@controller.delete("/{article_id}")
async def destroy(article_id: int, session: DatabaseSession):
    article = session.get(Article, article_id)
    if article:
        session.delete(article)
        session.commit()
    return {"status": "deleted"}
```

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

## Next Steps

* Manage database schemas: [Schema Migrations](/database/migrations).
* Protect routes with auth: [Authentication Starter Kit](/security/authentication).
