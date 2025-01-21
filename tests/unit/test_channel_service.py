# tests/unit/test_channel_service.py
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.subscription import Subscription
from app.schemas.channel import ChannelCreate
from app.services.channel_service import ChannelService
from app.services.huginn_client import HuginnClient
from tests.factories.channel import create_test_channel


class TestChannelService:
    def test_extract_channel_name_from_url(self, channel_service: ChannelService):
        url = "https://t.me/test_channel"
        channel_name = channel_service._extract_channel_name_from_url(url)
        assert channel_name == "test_channel"

    def test_create_duplicate_channel(
        self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session
    ):
        # Создаем первый канал через фабрику
        channel = create_test_channel(channel_name="test_channel")
        db_session.add(channel)
        db_session.commit()
        
        # Пытаемся создать тот же канал
        new_channel_data = ChannelCreate(
            channel_url="https://t.me/test_channel",
            callback_url="https://example.com/webhook"
        )
        
        with pytest.raises(HTTPException) as exc:
            channel_service.create_channel(new_channel_data)
        assert exc.value.status_code == 400
        assert "Channel already exists" in str(exc.value.detail)

    def test_delete_channel_calls_huginn_client(
        self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session
    ):
        # Создаем канал
        channel = Channel(
            channel_name="test_channel",
            is_monitored=True,
            huginn_rss_agent_id=1,
            huginn_post_agent_id=2
        )
        db_session.add(channel)
        db_session.flush()
        
        # Создаем подписку
        subscription = Subscription(
            channel_id=channel.id,
            callback_url="https://example.com/webhook"
        )
        db_session.add(subscription)
        db_session.commit()

        channel_service.delete_channel(channel.id)

        mock_huginn_client.delete_agent.assert_any_call(1)
        mock_huginn_client.delete_agent.assert_any_call(2)
        assert mock_huginn_client.delete_agent.call_count == 2

    def test_delete_channel_huginn_failure(
        self, channel_service: ChannelService, mock_huginn_client: MagicMock, db_session: Session
    ):
        # Создаем канал с существующими агентами
        channel = Channel(
            channel_name="test_channel",
            is_monitored=True,
            huginn_rss_agent_id=1,
            huginn_post_agent_id=2
        )
        db_session.add(channel)
        db_session.flush()
        
        # Создаем подписку
        subscription = Subscription(
            channel_id=channel.id,
            callback_url="https://example.com/webhook"
        )
        db_session.add(subscription)
        db_session.commit()

        mock_huginn_client.delete_agent.side_effect = Exception("Huginn deletion error")

        with pytest.raises(Exception) as exc:
            channel_service.delete_channel(channel.id)
        assert str(exc.value) == "Huginn deletion error" 