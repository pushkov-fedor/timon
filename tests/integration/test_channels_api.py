# tests/integration/test_channels_api.py
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories.channel import create_test_channel


class TestChannelsAPI:
    def test_create_channel(self, client: TestClient, db_session: Session, mock_huginn_client: MagicMock):
        response = client.post(
            "/channels/",
            json={"channel_url": "https://t.me/test_channel"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["channel_name"] == "test_channel"

        # Проверяем, что методы HuginnClient были вызваны
        mock_huginn_client.create_rss_agent.assert_called_once_with("test_channel")
        mock_huginn_client.create_post_agent.assert_called_once_with("test_channel")
        mock_huginn_client.link_agents.assert_called_once()

    def test_create_duplicate_channel(self, client: TestClient, db_session: Session, mock_huginn_client: MagicMock):
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

        # Проверяем, что второе создание агента не произошло
        assert mock_huginn_client.create_rss_agent.call_count == 1
        assert mock_huginn_client.create_post_agent.call_count == 1
        assert mock_huginn_client.link_agents.call_count == 1

    def test_create_channel_invalid_url(self, client: TestClient):
        response = client.post(
            "/channels/",
            json={"channel_url": "not_a_url"}
        )
        assert response.status_code == 422

    def test_delete_channel(self, client: TestClient, db_session: Session, mock_huginn_client: MagicMock):
        # Создаем канал
        response = client.post(
            "/channels/",
            json={"channel_url": "https://t.me/test_channel"}
        )
        assert response.status_code == 200
        channel_id = response.json()["id"]

        # Удаляем канал
        response = client.delete(f"/channels/{channel_id}")
        assert response.status_code == 204

        # Проверяем, что методы удаления агентов были вызваны
        mock_huginn_client.delete_agent.assert_any_call(1)  # Assuming huginn_rss_agent_id=1
        mock_huginn_client.delete_agent.assert_any_call(2)  # Assuming huginn_post_agent_id=2
        assert mock_huginn_client.delete_agent.call_count == 2

    def test_delete_nonexistent_channel(self, client: TestClient):
        response = client.delete("/channels/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Channel not found"