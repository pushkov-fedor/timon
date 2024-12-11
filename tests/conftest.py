# ./tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.repositories.channel_repository import ChannelRepository
from app.services.channel_service import ChannelService

# Используем тестовую базу PostgreSQL
engine = create_engine(settings.get_database_url)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def db_session() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        db.rollback()

@pytest.fixture
def client(db_session: Session) -> TestClient:
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