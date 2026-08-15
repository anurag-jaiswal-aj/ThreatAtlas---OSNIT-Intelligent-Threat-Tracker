import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

SECRET_KEY = getattr(settings, "SECRET_KEY", "threat_atlas_secret_key_2026_jwt_token_secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    """Hash a raw string password using HMAC-SHA256."""
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a raw string password against a hashed password."""
    expected = hash_password(plain_password)
    return hmac.compare_digest(expected, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    """
    FastAPI security dependency validating JWT Bearer tokens.
    For development / analyst testing, if no token is provided, returns default analyst session.
    If an invalid token is explicitly supplied, raises 401 Unauthorized.
    """
    if not credentials:
        # Default unauthenticated session for analyst convenience
        return {"sub": "analyst@threatatlas.internal", "role": "analyst"}

    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
