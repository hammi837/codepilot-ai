from datetime import timedelta

from app.core import security
from app.core.config import settings


def test_hash_and_verify_password() -> None:
    raw = "mysecret"
    hashed = security.hash_password(raw)
    assert hashed != raw
    assert security.verify_password(raw, hashed) is True


def test_create_and_verify_token() -> None:
    data = {"sub": "1"}
    token = security.create_access_token(data, expires_delta=timedelta(minutes=5))
    payload = security.verify_token(token)
    assert payload.get("sub") == "1"
    assert "exp" in payload
