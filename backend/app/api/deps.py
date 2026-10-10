from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.email import EmailSender, build_email_sender
from app.services.lead_service import LeadService
from app.services.storage import LocalStorage, StorageBackend

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]


def get_storage(settings: SettingsDep) -> StorageBackend:
    return LocalStorage(settings.upload_dir)


def get_email_sender(settings: SettingsDep) -> EmailSender:
    return build_email_sender(settings)


def get_lead_service(
    db: DbDep, settings: SettingsDep, storage: Annotated[StorageBackend, Depends(get_storage)]
) -> LeadService:
    return LeadService(db, storage, settings)


def get_auth_service(db: DbDep, settings: SettingsDep) -> AuthService:
    return AuthService(db, settings)


_bearer = HTTPBearer(auto_error=False)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    """Return the raw bearer token from the Authorization header, or raise 401."""
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    return credentials.credentials


BearerToken = Annotated[str, Depends(get_bearer_token)]


def get_current_user(
    auth: Annotated[AuthService, Depends(get_auth_service)], token: BearerToken
) -> User:
    """Resolve the bearer token to its user. Add `CurrentUser` to protect a route."""
    return auth.user_from_token(token)


EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
LeadServiceDep = Annotated[LeadService, Depends(get_lead_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
