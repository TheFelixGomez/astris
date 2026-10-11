from typing import NoReturn

from starlette.requests import Request

from astris.http import has_session


def test_has_session_with_active_session_in_scope():
    # Arrange
    scope = {"type": "http", "session": {"user_id": 123}}
    req = Request(scope)

    # Act
    result = has_session(req)

    # Assert
    assert result is True


def test_has_session_without_session_in_scope():
    # Arrange
    scope = {"type": "http"}
    req = Request(scope)

    # Act
    result = has_session(req)

    # Assert
    assert result is False


def test_has_session_fallback_without_scope():
    # Arrange
    class RequestWithoutScope(Request):
        def __init__(self) -> None:
            super().__init__({"type": "http"})
            self._scope_override: None = None

        @property
        def scope(self) -> None:
            return self._scope_override

        @scope.setter
        def scope(self, value: object) -> None:
            pass

        @property
        def session(self) -> dict[str, int]:
            return {"user_id": 456}

    req = RequestWithoutScope()

    # Act
    result = has_session(req)

    # Assert
    assert result is True


def test_has_session_fallback_with_broken_session():
    # Arrange
    class BrokenSessionRequest(Request):
        def __init__(self) -> None:
            super().__init__({"type": "http"})
            self._scope_override: None = None

        @property
        def scope(self) -> None:
            return self._scope_override

        @scope.setter
        def scope(self, value: object) -> None:
            pass

        @property
        def session(self) -> NoReturn:
            raise AssertionError("Broken session access")

    req = BrokenSessionRequest()

    # Act
    result = has_session(req)

    # Assert
    assert result is False
