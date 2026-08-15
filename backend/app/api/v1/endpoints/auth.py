from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status
from app.core.security import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email / login")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse, summary="Generate JWT Access Token")
async def login(payload: LoginRequest):
    """
    Exchanges analyst / admin credentials for a signed JWT access token.
    For project development, accepts any valid email format with matching password length >= 6.
    """
    if not payload.email or len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Password must be at least 6 characters.",
        )

    role = "admin" if "admin" in payload.email.lower() else "analyst"
    token_data = {"sub": payload.email, "role": role}
    access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={"email": payload.email, "role": role},
    )
