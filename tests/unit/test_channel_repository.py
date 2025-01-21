from app.repositories.channel_repository import ChannelRepository
from tests.factories.channel import create_test_channel


class TestChannelRepository:
    def test_create_channel(self, channel_repository: ChannelRepository):
        channel = create_test_channel()
        saved_channel = channel_repository.create(channel)
        assert saved_channel.id is not None
        assert saved_channel.channel_name == "test_channel"
        assert saved_channel.is_monitored is True

    def test_get_by_channel_name(self, channel_repository: ChannelRepository):
        channel = create_test_channel()
        channel_repository.create(channel)
        
        found_channel = channel_repository.get_by_channel_name("test_channel")
        assert found_channel is not None
        assert found_channel.channel_name == "test_channel"
        assert found_channel.is_monitored is True

    def test_get_by_channel_name_not_found(self, channel_repository: ChannelRepository):
        found_channel = channel_repository.get_by_channel_name("nonexistent")
        assert found_channel is None 