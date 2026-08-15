import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token, verify_token, hash_password, verify_password

client = TestClient(app)


def test_password_hashing():
    raw_pass = "SecureAnalystPassword123"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_verification():
    payload = {"sub": "analyst@threatatlas.internal", "role": "analyst"}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == "analyst@threatatlas.internal"
    assert decoded["role"] == "analyst"


def test_invalid_jwt_token():
    invalid = verify_token("invalid.jwt.token.string")
    assert invalid is None


def test_auth_login_endpoint():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@threatatlas.internal", "password": "SecurePassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "analyst@threatatlas.internal"


def test_auth_login_invalid_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@threatatlas.internal", "password": "123"},
    )
    assert response.status_code == 401
