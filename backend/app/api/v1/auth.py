from fastapi import APIRouter, Response, status

from app.api.deps import AuthServiceDep, BearerToken, CurrentUser
from app.schemas.auth import LoginRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, auth: AuthServiceDep) -> TokenResponse:
    token, expires_in = auth.authenticate(body.email, body.password)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: BearerToken, auth: AuthServiceDep) -> Response:
    """Revoke the bearer token so it can't be used again, even before it expires."""
    auth.revoke_token(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
