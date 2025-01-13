from app.models.channel import Channel


def create_test_channel(
    channel_name: str = "test_channel",
    callback_url: str = "https://example.com/webhook"
) -> Channel:
    """Создает объект Channel для тестов"""
    return Channel(
        channel_name=channel_name,
        callback_url=callback_url,
        is_monitored=True,
        huginn_rss_agent_id=1,
        huginn_post_agent_id=2
    ) 