# ./tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Используем тестовую базу PostgreSQL
engine = create_engine(settings.get_database_url)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def db_session():
    Base.metadata.drop_all(bind=engine)  # Сначала удаляем все таблицы
    Base.metadata.create_all(bind=engine)  # Создаем таблицы заново
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        db.rollback()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()