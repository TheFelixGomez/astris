from pathlib import Path

from sqlmodel import Field, SQLModel, select

from astris.database.session import Database, DatabaseSession, get_session


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


def test_database_lifecycle(tmp_path: Path):
    # Arrange
    from unittest.mock import patch

    db_instance = Database(base_path=tmp_path)
    db_custom = Database(
        url=f"sqlite:///{tmp_path / 'database' / 'app.db'}", base_path=tmp_path
    )

    # Act & Assert 1: Config URL
    assert db_instance.url == "sqlite:///database/app.db"

    # Act & Assert 2: Fallback when database_url is None
    with patch("astris.config.get_settings") as mock_settings:
        mock_settings.return_value.database_url = None
        db_fallback = Database(base_path=tmp_path)
        assert db_fallback.url == f"sqlite:///{tmp_path / 'database' / 'app.db'}"

    # Act & Assert 3: Engine instantiation and caching
    engine = db_custom.engine
    assert engine is not None
    assert db_custom.engine is engine

    # Act & Assert 4: Create tables and verify physical sqlite database creation
    db_custom.create_all()
    assert (tmp_path / "database" / "app.db").exists()

    # Act & Assert 5: Session context manager and CRUD operations
    with db_custom.session() as session:
        item = Item(name="Test Item")
        session.add(item)
        session.commit()
        session.refresh(item)
        assert item.id is not None

        result = session.exec(select(Item)).all()
        assert len(result) == 1
        assert result[0].name == "Test Item"

    # Act & Assert 6: Dependency generator get_session()
    gen = db_custom.get_session()
    s = next(gen)
    assert s is not None
    s.close()

    # Act & Assert 7: Reconfigure database
    db_custom.configure(url="sqlite:///:memory:", echo=True)
    assert db_custom.url == "sqlite:///:memory:"
    assert db_custom._engine is None
    new_engine = db_custom.engine
    assert new_engine is not engine
    assert new_engine.echo is True

    # Act & Assert 8: Drop all tables
    db_custom.create_all()
    db_custom.drop_all()


def test_global_get_session():
    # Arrange
    gen = get_session()

    # Act
    session = next(gen)

    # Assert
    assert session is not None
    session.close()
    assert DatabaseSession is not None


def test_missing_database_driver_diagnostic():
    import pytest

    # Arrange 1: PostgreSQL URL without driver
    db_pg = Database(url="postgresql://user:pass@localhost:5432/dbname")

    # Act & Assert 1
    with pytest.raises(RuntimeError) as exc_info:
        _ = db_pg.engine
    assert "Missing database driver" in str(exc_info.value)
    assert "uv add psycopg2-binary" in str(exc_info.value)

    # Arrange 2: MySQL URL without driver
    db_mysql = Database(url="mysql://user:pass@localhost:3306/dbname")
    with pytest.raises(RuntimeError) as exc_mysql:
        _ = db_mysql.engine
    assert "Missing database driver" in str(exc_mysql.value)
    assert "uv add pymysql" in str(exc_mysql.value)
