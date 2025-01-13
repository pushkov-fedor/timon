# tests/unit/test_channel_service.py
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.schemas.channel import ChannelCreate
from app.services.channel_service import ChannelService
from app.services.huginn_client import HuginnClient


class TestChannelService:
    def test_extract_channel_name_from_url(self, channel_service: ChannelService):
        url = "https://t.me/test_channel"
        channel_name = channel_service._extract_channel_name_from_url(url)
        assert channel_name == "test_channel"

    def test_create_channel_calls_huginn_client(self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session):
        channel_data = ChannelCreate(
            channel_url="https://t.me/test_channel",
            callback_url="https://example.com/webhook"
        )
        channel = channel_service.create_channel(channel_data)

        assert channel.channel_name == "test_channel"
        mock_huginn_client.create_rss_agent.assert_called_once_with("test_channel")
        mock_huginn_client.create_post_agent.assert_called_once_with("test_channel")
        mock_huginn_client.link_agents.assert_called_once()

    def test_create_duplicate_channel(self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session):
        channel_data = ChannelCreate(
            channel_url="https://t.me/test_channel",
            callback_url="https://example.com/webhook"
        )
        channel_service.create_channel(channel_data)

        with pytest.raises(HTTPException) as exc:
            channel_service.create_channel(channel_data)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Channel already exists"

    def test_delete_channel_calls_huginn_client(self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session):
        # Создаем канал
        channel = Channel(
            channel_name="test_channel",
            callback_url="https://example.com/webhook",
            is_monitored=True,
            huginn_rss_agent_id=1,
            huginn_post_agent_id=2
        )
        db_session.add(channel)
        db_session.commit()

        channel_service.delete_channel(channel.id)

        mock_huginn_client.delete_agent.assert_any_call(1)
        mock_huginn_client.delete_agent.assert_any_call(2)
        assert mock_huginn_client.delete_agent.call_count == 2

    def test_create_channel_huginn_failure(self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session):
        # Настраиваем HuginnClient так, чтобы create_rss_agent выбрасывал исключение
        mock_huginn_client.create_rss_agent.side_effect = Exception("Huginn error")

        channel_data = ChannelCreate(
            channel_url="https://t.me/test_channel",
            callback_url="https://example.com/webhook"
        )
        with pytest.raises(Exception) as exc:
            channel_service.create_channel(channel_data)
        assert str(exc.value) == "Huginn error"

    def test_delete_channel_huginn_failure(self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session):
        # Создаем канал с существующими агентами
        channel = Channel(
            channel_name="test_channel",
            callback_url="https://example.com/webhook",
            is_monitored=True,
            huginn_rss_agent_id=1,
            huginn_post_agent_id=2
        )
        db_session.add(channel)
        db_session.commit()

        # Настраиваем HuginnClient так, чтобы delete_agent выбрасывал исключение при попытке удалить агента
        mock_huginn_client.delete_agent.side_effect = Exception("Huginn deletion error")

        with pytest.raises(Exception) as exc:
            channel_service.delete_channel(channel.id)
        assert str(exc.value) == "Huginn deletion error" 