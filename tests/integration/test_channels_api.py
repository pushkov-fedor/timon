import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories.channel import create_test_channel


class TestChannelsAPI:
    def test_create_channel(self, client: TestClient, db_session: Session):
        response = client.post(
            "/channels/",
            json={"channel_url": "https://t.me/test_channel"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["channel_name"] == "test_channel"

    def test_create_duplicate_channel(self, client: TestClient, db_session: Session):
        # Создаем первый канал
        response = client.post(
            "/channels/",
            json={"channel_url": "https://t.me/test_channel"}
        )
        assert response.status_code == 200

        # Пытаемся создать дубликат
        response = client.post(
            "/channels/",
            json={"channel_url": "https://t.me/test_channel"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Channel already exists"

    def test_create_channel_invalid_url(self, client: TestClient):
        response = client.post(
            "/channels/",
            json={"channel_url": "not_a_url"}
        )
        assert response.status_code == 422 