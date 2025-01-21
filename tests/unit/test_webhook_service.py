from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.models.channel import Channel
from app.schemas.post import ParsedPost, PostWebhook
from app.services.webhook_service import WebhookService


def test_parse_html_content(webhook_service):
    """
    Test HTML content parsing from Telegram channel posts.
    Should correctly extract text, links, images and videos.
    """
    html = """
    <div class="tgme_widget_message_text js-message_text" dir="auto">
        <a href="https://t.me/test_channel/123">#test</a>
        <br>Test message content
        <br><a href="https://t.me/test_channel" target="_blank">@test_channel</a>
    </div>
    <img src="https://cdn4.cdn-telegram.org/file/example1.jpg"/>
    <img src="https://cdn4.cdn-telegram.org/file/example2.jpg"/>
    """
    
    text, links, images, videos = webhook_service._parse_html_content(html)

    assert isinstance(text, str)
    assert isinstance(links, list)
    assert isinstance(images, list)
    assert isinstance(videos, list)
    
    # Проверяем извлечение текста
    assert "Test message content" in text
    
    # Проверяем извлечение ссылок
    assert "https://t.me/test_channel" in links
    assert "https://t.me/test_channel/123" in links
    
    # Проверяем извлечение изображений
    assert len(images) == 2
    assert "https://cdn4.cdn-telegram.org/file/example1.jpg" in images
    assert "https://cdn4.cdn-telegram.org/file/example2.jpg" in images
    
    # Проверяем что видео нет
    assert len(videos) == 0


def test_parse_html_content_with_empty_content(webhook_service):
    """
    Test HTML parsing with empty content.
    Should return empty values.
    """
    text, links, images, videos = webhook_service._parse_html_content("")

    assert text == ""
    assert links == []
    assert images == []
    assert videos == []


def test_parse_html_content_with_video(webhook_service):
    """
    Test HTML parsing with video content.
    Should correctly extract video URLs.
    """
    html = """
    <div class="tgme_widget_message_text js-message_text" dir="auto">
        Post with video
    </div>
    <video src="https://cdn4.cdn-telegram.org/file/video123.mp4"></video>
    """
    
    text, links, images, videos = webhook_service._parse_html_content(html)

    assert "Post with video" in text
    assert len(videos) == 1
    assert "https://cdn4.cdn-telegram.org/file/video123.mp4" in videos[0] 


def test_extract_channel_name(webhook_service):
    """
    Test channel name extraction from Telegram URLs.
    """
    # Valid URLs
    assert webhook_service._extract_channel_name("https://t.me/test_channel") == "test_channel"
    assert webhook_service._extract_channel_name("https://t.me/test_channel/123") == "test_channel"
    assert webhook_service._extract_channel_name("https://t.me/my_channel_123/456?q=test") == "my_channel_123"
    
    # Invalid URLs
    assert webhook_service._extract_channel_name("invalid_url") == "invalid_url"  # Текущее поведение метода
    assert webhook_service._extract_channel_name("https://example.com") == ""
    assert webhook_service._extract_channel_name("") == ""


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client"""
    client = MagicMock()
    client.post = AsyncMock()
    client.post.return_value.status_code = 200
    return client


@pytest.fixture
def webhook_service(db_session):
    """Create WebhookService instance with mocked HTTP client"""
    service = WebhookService(db_session)
    service.http_client = MagicMock()
    service.http_client.post = AsyncMock()
    service.http_client.post.return_value.status_code = 200
    return service


@pytest.mark.asyncio
async def test_send_to_callback(webhook_service, mock_http_client):
    """Test sending parsed post to callback URL."""
    webhook_service.http_client = mock_http_client
    
    post = ParsedPost(
        title="Test Post",
        link="https://t.me/test_channel/123",
        guid="test_guid",
        published_at=datetime.utcnow(),
        text="Test content",
        links=["https://example.com"],
        images=["https://example.com/image.jpg"],
        videos=["https://example.com/video.mp4"],
        channel_name="test_channel",
        raw_content="<div>Test content</div>"
    )
    
    await webhook_service._send_to_callback("http://test-callback.com", post)
    
    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    assert call_args[1]["url"] == "http://test-callback.com"
    assert call_args[1]["headers"]["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_send_to_callback_failure(webhook_service, mock_http_client):
    """Test handling of callback failures."""
    webhook_service.http_client = mock_http_client
    mock_http_client.post.return_value.status_code = 500
    mock_http_client.post.return_value.text = "Internal Server Error"
    
    with pytest.raises(HTTPException) as exc_info:
        await webhook_service._send_to_callback(
            "http://test-callback.com",
            ParsedPost(
                title="Test",
                link="https://t.me/test/1",
                guid="1",
                published_at=datetime.utcnow(),
                text="test",
                links=[],
                images=[],
                videos=[],
                channel_name="test",
                raw_content="test"
            )
        )
    
    assert exc_info.value.status_code == 500
    assert "Failed to send callback request" in str(exc_info.value.detail) 


def test_parse_rfc822_date(webhook_service):
    """Test parsing RFC 822 date format."""
    test_date = "2024-01-14T12:00:00Z"  # ISO format date string
    
    parsed_date = webhook_service._parse_rfc822_date(test_date)
    assert parsed_date.year == 2024
    assert parsed_date.month == 1
    assert parsed_date.day == 14
    assert parsed_date.hour == 12
    assert parsed_date.minute == 0


@pytest.mark.asyncio
async def test_webhook_service_context_manager():
    """Test WebhookService as async context manager."""
    from app.db.session import get_db
    db = next(get_db())
    
    async with WebhookService(db) as service:
        assert isinstance(service.http_client, httpx.AsyncClient)
        assert not service.http_client.is_closed
    
    assert service.http_client.is_closed


def test_webhook_service_init():
    """Test WebhookService initialization."""
    from app.db.session import get_db
    db = next(get_db())
    
    service = WebhookService(db)
    assert service.repository is not None
    assert isinstance(service.http_client, httpx.AsyncClient)
    assert service.http_client.timeout.read == 30.0


@pytest.mark.asyncio
async def test_process_webhook_success(webhook_service):
    """Test successful webhook processing"""
    from app.models.subscription import Subscription
    from tests.factories.post import create_test_post_webhook
    
    # Create test data
    post = create_test_post_webhook(
        url="https://t.me/test_channel/1234",
        title="Test Post",
        description="<p>Test content with <a href='https://example.com'>link</a></p>"
    )
    
    # Mock repository methods
    with patch.object(webhook_service.repository, 'get_by_channel_name') as mock_get, \
         patch.object(webhook_service.subscription_repository, 'get_active_by_channel_id') as mock_get_subs:
        
        channel = Channel(
            id=1,
            channel_name="test_channel",
            is_monitored=True
        )
        subscription = Subscription(
            channel_id=1,
            callback_url="http://callback.com/webhook",
            is_active=True
        )
        
        mock_get.return_value = channel
        mock_get_subs.return_value = [subscription]
        
        # Mock HTTP client
        webhook_service.http_client.post.return_value = AsyncMock(
            status_code=200,
            json=AsyncMock(return_value={"status": "success"})
        )
        
        # Process webhook
        await webhook_service.process_post(post)
        
        # Verify channel was looked up
        mock_get.assert_called_once_with("test_channel")
        mock_get_subs.assert_called_once_with(1)
        
        # Verify callback was called
        webhook_service.http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_process_webhook_channel_not_found(webhook_service):
    """Test webhook processing when channel is not found"""
    from tests.factories.post import create_test_post_webhook
    
    post = create_test_post_webhook(url="https://t.me/test_channel/1234")
    
    # Mock repository to return None
    with patch.object(webhook_service.repository, 'get_by_channel_name') as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await webhook_service.process_post(post)
        
        assert exc_info.value.status_code == 404
        assert "Channel not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_process_webhook_invalid_url(webhook_service):
    """Test webhook processing with invalid Telegram URL"""
    from tests.factories.post import create_test_post_webhook
    
    # Create post with non-Telegram URL
    post = create_test_post_webhook(url="https://invalid-url.com/1234")
    
    # Mock repository to return None since channel won't be found
    with patch.object(webhook_service.repository, 'get_by_channel_name') as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await webhook_service.process_post(post)
        
        assert exc_info.value.status_code == 404
        assert "Channel not found" in str(exc_info.value.detail)
        
        # Verify repository was called with extracted channel name
        mock_get.assert_called_once()