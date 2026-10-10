import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    """Body of `POST /auth/login`."""

    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    """Body of `POST /auth/change-password`. The password policy is enforced in AuthService."""

    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    """A new bearer token; `expires_in` is its lifetime in seconds."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserRead(BaseModel):
    """The signed-in user, as returned by `GET /auth/me`."""

    id: uuid.UUID
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)
