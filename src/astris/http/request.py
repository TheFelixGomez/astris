from fastapi import Request


def has_session(request: Request) -> bool:
    """Safely check if a request has an active session in its scope without triggering assertion errors."""
    scope = getattr(request, "scope", None)
    if isinstance(scope, dict):
        return "session" in scope
    try:
        return hasattr(request, "session")
    except (AssertionError, AttributeError):
        return False
