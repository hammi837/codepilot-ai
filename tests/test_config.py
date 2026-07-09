import pytest
from pydantic import ValidationError

from app.core import config


def clear_settings_cache() -> None:
    config.get_settings.cache_clear()


def test_settings_read_values_from_env_file(tmp_path) -> None:
    clear_settings_cache()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "PROJECT_NAME=Demo App\n"
        "VERSION=2.0.0\n"
        "DEBUG=True\n"
        "HOST=127.0.0.1\n"
        "PORT=9000\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=demo\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=postgres\n"
        "SECRET_KEY=super-secret-key\n"
        "ALGORITHM=HS512\n"
        "ACCESS_TOKEN_EXPIRE_MINUTES=90\n",
        encoding="utf-8",
    )

    settings = config.Settings(_env_file=env_file)

    assert settings.PROJECT_NAME == "Demo App"
    assert settings.VERSION == "2.0.0"
    assert settings.DEBUG is True
    assert settings.HOST == "127.0.0.1"
    assert settings.PORT == 9000
    assert settings.DATABASE_URL == "postgresql://postgres:postgres@localhost:5432/demo"
    assert settings.SECRET_KEY == "super-secret-key"
    assert settings.ALGORITHM == "HS512"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 90


def test_missing_required_values_raise_validation_error(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("PROJECT_NAME=Demo App\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        config.Settings(_env_file=env_file)


def test_get_settings_is_cached() -> None:
    clear_settings_cache()

    first = config.get_settings()
    second = config.get_settings()

    assert first is second
