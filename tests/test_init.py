import astris
import astris.auth
import astris.database
import astris.http
import astris.inertia
import astris.routing
import astris.security


def test_top_level_init():
    # Arrange
    expected_attrs = ["Astris", "Settings", "__version__"]

    # Act & Assert
    for attr in expected_attrs:
        assert hasattr(astris, attr)
        assert attr in astris.__all__
    assert astris.__version__ == "0.1.6"


def test_http_init():
    # Arrange
    expected_attrs = [
        "Request",
        "Response",
        "RedirectResponse",
        "JSONResponse",
        "HTMLResponse",
    ]

    # Act & Assert
    for attr in expected_attrs:
        assert hasattr(astris.http, attr)
    assert "Request" in astris.http.__all__


def test_routing_init():
    # Arrange
    expected_attrs = ["Controller", "has_route"]

    # Act & Assert
    for attr in expected_attrs:
        assert hasattr(astris.routing, attr)
        assert attr in astris.routing.__all__


def test_security_init():
    # Arrange
    expected_attr = "CSRFMiddleware"

    # Act & Assert
    assert hasattr(astris.security, expected_attr)
    assert expected_attr in astris.security.__all__


def test_database_init():
    # Arrange
    expected_attrs = [
        "Database",
        "DatabaseSession",
        "db",
        "SQLModel",
        "Field",
        "Session",
        "asc",
        "desc",
    ]

    # Act & Assert
    for attr in expected_attrs:
        assert hasattr(astris.database, attr)
    assert "asc" in astris.database.__all__
    assert "desc" in astris.database.__all__


def test_inertia_init():
    # Arrange
    expected_attrs = ["InertiaResponse", "share", "flash"]

    # Act & Assert
    for attr in expected_attrs:
        assert hasattr(astris.inertia, attr)
        assert attr in astris.inertia.__all__


def test_auth_init():
    # Arrange
    expected_attrs = [
        "hash_password",
        "verify_password",
        "verify_and_update_password",
        "login_user",
        "logout_user",
        "get_user_id",
        "get_auth_user",
        "is_authenticated",
        "auth_required",
        "guest_required",
        "AuthUser",
        "AuthUserId",
    ]

    # Act & Assert
    for attr in expected_attrs:
        assert hasattr(astris.auth, attr)
    assert "hash_password" in astris.auth.__all__
