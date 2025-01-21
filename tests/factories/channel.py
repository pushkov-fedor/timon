from app.models.channel import Channel


def create_test_channel(
    channel_name: str = "test_channel",
    is_monitored: bool = True,
    huginn_rss_agent_id: int | None = None,
    huginn_post_agent_id: int | None = None
) -> Channel:
    """Создает объект Channel для тестов"""
    return Channel(
        channel_name=channel_name,
        is_monitored=is_monitored,
        huginn_rss_agent_id=huginn_rss_agent_id,
        huginn_post_agent_id=huginn_post_agent_id
    ) 