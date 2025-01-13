# ./tests/conftest.py
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.repositories.channel_repository import ChannelRepository
from app.services.channel_service import ChannelService
from app.services.huginn_client import HuginnClient
from app.services.webhook_service import WebhookService
from tests.factories.post import create_test_html_content, create_test_post_webhook


@pytest.fixture(autouse=True)
def mock_huginn_client(monkeypatch):
    """
    Мокирование HuginnClient для избежания реальных HTTP-запросов к Huginn.
    """
    mock = MagicMock(spec=HuginnClient)

    # Настройка возвращаемых значений для методов HuginnClient
    mock.create_rss_agent.return_value = 1
    mock.create_post_agent.return_value = 2
    mock.link_agents.return_value = None
    mock.delete_agent.return_value = None
    mock.get_agent_status.return_value = {"status": "ok"}

    # Патчинг HuginnClient в модуле, где он используется
    monkeypatch.setattr('app.services.channel_service.HuginnClient', lambda: mock)

    return mock


@pytest.fixture(scope="session")
def engine():
    from app.db.session import engine
    return engine


@pytest.fixture(autouse=True)
def db_session(engine) -> Session:
    """
    Фикстура для настройки тестовой базы данных.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """
    Фикстура для тестового клиента FastAPI с переопределенными зависимостями.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def channel_repository(db_session: Session) -> ChannelRepository:
    return ChannelRepository(db_session)


@pytest.fixture
def channel_service(db_session: Session) -> ChannelService:
    return ChannelService(db_session)


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client for testing webhook callbacks."""
    mock = MagicMock()
    mock.post.return_value = MagicMock(
        status_code=200,
        text="OK"
    )
    return mock


@pytest.fixture
def webhook_service(db_session: Session, mock_http_client: MagicMock) -> WebhookService:
    """Create WebhookService instance with mocked HTTP client for testing."""
    service = WebhookService(db_session)
    service.http_client = mock_http_client
    return service


@pytest.fixture
def sample_html_content() -> str:
    """Return sample HTML content similar to a Telegram channel post."""
    return create_test_html_content(
        text="Test post content",
        links=["https://example.com"],
        images=["https://example.com/image.jpg"],
        videos=["https://example.com/video.mp4"]
    )


@pytest.fixture
def sample_webhook_post() -> dict:
    """Return sample webhook post data."""
    post = create_test_post_webhook(
        title="Test Channel Post",
        url="https://t.me/test_channel/123",
        description=create_test_html_content()
    )
    return post.model_dump()