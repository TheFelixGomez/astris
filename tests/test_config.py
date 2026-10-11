from astris.config import Settings, get_settings


def test_settings_defaults():
    # Arrange & Act
    settings = Settings()

    # Assert
    assert settings.app_name == "Astris Application"
    assert settings.app_env == "local"
    assert settings.app_debug is True
    assert settings.app_key == ""
    assert settings.database_url == "sqlite:///database/app.db"
    assert settings.db_echo is False
    assert settings.auto_create_tables is None
    assert settings.resolved_auto_create_tables is True
    assert settings.session_cookie_name == "astris_session"
    assert settings.session_max_age == 14 * 24 * 60 * 60
    assert settings.session_https_only is None
    assert settings.session_same_site == "lax"
    assert "http://localhost:5173" in settings.cors_origins
    assert settings.enable_csrf is True
    assert settings.csrf_exempt_paths == []


def test_settings_production_properties():
    # Arrange
    env_local = "local"
    env_prod = "production"
    env_prod_short = "prod"

    # Act
    settings_local = Settings(app_env=env_local)
    settings_prod = Settings(app_env=env_prod)
    settings_prod_short = Settings(app_env=env_prod_short)
    settings_override_true = Settings(app_env=env_local, session_https_only=True)
    settings_override_false = Settings(app_env=env_prod, session_https_only=False)
    settings_tables_override = Settings(app_env=env_prod, auto_create_tables=True)

    # Assert
    assert settings_local.is_production is False
    assert settings_local.resolved_session_https_only is False
    assert settings_local.resolved_auto_create_tables is True

    assert settings_prod.is_production is True
    assert settings_prod.resolved_session_https_only is True
    assert settings_prod.resolved_auto_create_tables is False

    assert settings_prod_short.is_production is True
    assert settings_prod_short.resolved_session_https_only is True
    assert settings_prod_short.resolved_auto_create_tables is False

    assert settings_override_true.resolved_session_https_only is True
    assert settings_override_false.resolved_session_https_only is False
    assert settings_tables_override.resolved_auto_create_tables is True


def test_get_settings_cached():
    # Arrange & Act
    instance_one = get_settings()
    instance_two = get_settings()

    # Assert
    assert instance_one is instance_two
