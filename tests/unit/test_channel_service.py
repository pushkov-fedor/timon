import pytest
from fastapi import HTTPException

from app.schemas.channel import ChannelCreate
from app.services.channel_service import ChannelService


class TestChannelService:
    def test_extract_channel_name_from_url(self, channel_service: ChannelService):
        url = "https://t.me/test_channel"
        channel_name = channel_service._extract_channel_name_from_url(url)
        assert channel_name == "test_channel"

    def test_create_channel(self, channel_service: ChannelService):
        channel_data = ChannelCreate(channel_url="https://t.me/test_channel")
        channel = channel_service.create_channel(channel_data)
        assert channel.channel_name == "test_channel"

    def test_create_duplicate_channel(self, channel_service: ChannelService):
        channel_data = ChannelCreate(channel_url="https://t.me/test_channel")
        channel_service.create_channel(channel_data)

        with pytest.raises(HTTPException) as exc:
            channel_service.create_channel(channel_data)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Channel already exists" 