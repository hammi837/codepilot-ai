import importlib

from fastapi.testclient import TestClient


def test_database_components_are_initialized(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    import app.db.session as session_module

    session_module = importlib.reload(session_module)

    assert session_module.engine is not None
    assert session_module.SessionLocal is not None


def test_get_db_yields_a_session(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    import app.db.session as session_module
    import app.main as main_module

    session_module = importlib.reload(session_module)
    main_module = importlib.reload(main_module)

    client = TestClient(main_module.app)
    response = client.get("/db-test")

    assert response.status_code == 200
    assert response.json() == {"database": "connected"}
