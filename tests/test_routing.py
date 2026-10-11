from enum import Enum

from fastapi import APIRouter, FastAPI

from astris.routing import (
    Body,
    Controller,
    Cookie,
    Depends,
    File,
    Form,
    Header,
    Path,
    PathParam,
    Query,
    Security,
    UploadFile,
    has_route,
    status,
)


def test_routing_reexports():
    # Arrange
    symbols = [
        Controller,
        Body,
        Cookie,
        Depends,
        File,
        Form,
        Header,
        Path,
        PathParam,
        Query,
        Security,
        UploadFile,
    ]

    # Act & Assert
    for symbol in symbols:
        assert symbol is not None
    assert status.HTTP_200_OK == 200


def test_controller_instantiation():
    # Arrange
    prefix = "/users"
    tags: list[str | Enum] = ["Users"]

    # Act
    controller = Controller(prefix=prefix, tags=tags)

    # Assert
    assert controller.prefix == prefix
    assert controller.tags == tags


def test_has_route():
    # Arrange
    app = FastAPI()

    # Direct route on app
    @app.get("/direct")
    def direct_route() -> dict[str, str]:
        return {"msg": "direct"}

    # Controller router
    controller = Controller(prefix="/api")

    @controller.get("/items")
    def list_items() -> list[str]:
        return []

    app.include_router(controller)

    # Subrouter nested inside another router
    nested_router = APIRouter(prefix="/sub")

    @nested_router.get("/detail")
    def sub_detail() -> dict[str, str]:
        return {}

    parent_router = APIRouter(prefix="/parent")
    parent_router.include_router(nested_router)
    app.include_router(parent_router)

    class DummyTarget:
        def __init__(self, target_app: object) -> None:
            self.app = target_app

    target = DummyTarget(app)

    class DummySubRoute:
        def __init__(self, path: str) -> None:
            self.path = path

    class DummyParentRoute:
        def __init__(self, routes: list[DummySubRoute]) -> None:
            self.routes = routes

    class DummyAppWithRoutes:
        def __init__(self) -> None:
            self.routes = [DummyParentRoute([DummySubRoute("/nested-mount")])]

    # Act & Assert
    assert has_route(app, "/direct") is True
    assert has_route(app, "/api/items") is True
    assert has_route(app, "/parent/sub/detail") is True
    assert has_route(app, "/non-existent") is False
    assert has_route(target, "/direct") is True
    assert has_route(target, "/unknown") is False
    assert has_route(object(), "/direct") is False
    assert has_route(DummyAppWithRoutes(), "/nested-mount") is True
