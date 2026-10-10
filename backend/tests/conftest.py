from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_email_sender, get_storage
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.services.auth_service import AuthService
from app.services.email import ConsoleEmailSender
from app.services.storage import LocalStorage

PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
ATTORNEY_EMAIL = "attorney@firm.example.com"
ATTORNEY_PASSWORD = "s3cret-password"


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        environment="test",
        database_url="sqlite://",
        upload_dir=str(tmp_path / "uploads"),
        jwt_secret="test-secret-that-is-at-least-32-bytes-long",
        attorney_notification_email="intake@firm.example.com",
        frontend_base_url="http://frontend.test",
        max_resume_bytes=1024 * 1024,
    )


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def db(session_factory) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def outbox() -> ConsoleEmailSender:
    return ConsoleEmailSender()


@pytest.fixture
def client(settings, session_factory, outbox) -> Iterator[TestClient]:
    app = create_app()

    def override_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_storage] = lambda: LocalStorage(settings.upload_dir)
    app.dependency_overrides[get_email_sender] = lambda: outbox
    with TestClient(app) as c:
        yield c


@pytest.fixture
def attorney(db, settings):
    return AuthService(db, settings).create_user(
        email=ATTORNEY_EMAIL, password=ATTORNEY_PASSWORD, full_name="Ada Attorney"
    )


@pytest.fixture
def auth_headers(client, attorney) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD}
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def submit_lead(client: TestClient, **overrides):
    data = {"first_name": "Grace", "last_name": "Hopper", "email": "grace@example.com"}
    files_override = overrides.pop("files", None)
    data.update(overrides)
    files = files_override or {"resume": ("resume.pdf", PDF_BYTES, "application/pdf")}
    return client.post("/api/v1/leads", data=data, files=files)
