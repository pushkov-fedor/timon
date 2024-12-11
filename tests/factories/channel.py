from app.models.channel import Channel


def create_test_channel(channel_name: str = "test_channel") -> Channel:
    """Создает объект Channel для тестов"""
    return Channel(
        channel_name=channel_name,
        is_monitored=True
    ) 