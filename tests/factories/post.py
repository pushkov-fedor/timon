from datetime import datetime, timezone
from typing import Optional

from app.schemas.post import ParsedPost, PostWebhook


def create_test_post_webhook(
    id: str = "test_post_1",
    url: str = "https://t.me/test_channel/1234",
    title: str = "Test Post",
    description: str = "<p>Test content with <a href='https://example.com'>link</a></p>",
    content: str = "Test content",
    date_published: Optional[str] = None,
    last_updated: Optional[str] = None
) -> PostWebhook:
    """Create a test PostWebhook instance with RSS-like content"""
    if date_published is None:
        date_published = datetime.now(timezone.utc).isoformat()
    if last_updated is None:
        last_updated = date_published

    return PostWebhook(
        id=id,
        url=url,
        title=title,
        description=description,
        content=content,
        date_published=date_published,
        last_updated=last_updated
    )

def create_test_parsed_post(
    title: str = "Test Post",
    link: str = "https://t.me/test_channel/1234",
    guid: str = "test_post_1",
    published_at: Optional[datetime] = None,
    text: str = "Test content",
    links: list[str] = None,
    images: list[str] = None,
    videos: list[str] = None,
    channel_name: str = "test_channel",
    raw_content: Optional[str] = None
) -> ParsedPost:
    """Create a test ParsedPost instance with typical Telegram channel content"""
    if published_at is None:
        published_at = datetime.now(timezone.utc)
    if links is None:
        links = ["https://example.com"]
    if images is None:
        images = ["https://example.com/image.jpg"]
    if videos is None:
        videos = ["https://example.com/video.mp4"]
    if raw_content is None:
        raw_content = create_test_html_content(text, links, images, videos)

    return ParsedPost(
        title=title,
        link=link,
        guid=guid,
        published_at=published_at,
        text=text,
        links=links,
        images=images,
        videos=videos,
        channel_name=channel_name,
        raw_content=raw_content
    )

def create_test_html_content(
    text: str = "Test content",
    links: list[str] = None,
    images: list[str] = None,
    videos: list[str] = None,
    include_telegram_classes: bool = True
) -> str:
    """
    Create test HTML content similar to Telegram channel post
    
    Args:
        text: Main text content
        links: List of URLs to include as links
        images: List of image URLs
        videos: List of video URLs
        include_telegram_classes: Whether to include Telegram-specific CSS classes
    """
    if links is None:
        links = ["https://example.com"]
    if images is None:
        images = ["https://example.com/image.jpg"]
    if videos is None:
        videos = ["https://example.com/video.mp4"]

    div_class = 'class="tgme_widget_message_text js-message_text"' if include_telegram_classes else ''
    
    html_parts = [f'<div {div_class} dir="auto">']
    html_parts.append(f"<p>{text}</p>")
    
    # Add hashtags like in real Telegram posts
    html_parts.append('<a href="/test_channel/123?q=%23test">#test</a>')
    
    for link in links:
        html_parts.append(f'<a href="{link}">Link</a>')
    
    html_parts.append("</div>")
    
    # Add media content outside the text div
    for img in images:
        html_parts.append(f'<img src="{img}" width="800" height="800" referrerpolicy="no-referrer">')
    
    for video in videos:
        html_parts.append(
            f'<video src="{video}" controls="controls" poster="https://example.com/poster.jpg" '
            'style="width:100%"></video>'
        )
    
    return "\n".join(html_parts) 