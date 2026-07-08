import importlib


def test_database_components_are_initialized(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    import app.db.session as session_module

    session_module = importlib.reload(session_module)

    assert session_module.engine is not None
    assert session_module.SessionLocal is not None
