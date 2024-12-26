# app/services/webhook_service.py

import logging
import time
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

from app.core.exceptions.http_exceptions import ChannelNotFound
from app.repositories.channel_repository import ChannelRepository
from app.schemas.post import ParsedPost, PostWebhook
from app.utils.retry import async_retry

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self, db):
        self.repository = ChannelRepository(db)
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    def _extract_channel_name(self, url: str) -> str:
        """Extract channel name from Telegram post URL"""
        parsed = urlparse(str(url))
        path_parts = parsed.path.strip('/').split('/')
        return path_parts[0] if len(path_parts) > 0 else None

    def _parse_html_content(self, html: str) -> tuple[str, list[str], list[str], list[str]]:
        """Parse HTML content to extract text, links, images and videos"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract text (remove all scripts and styles first)
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ').strip()
        
        # Extract links (excluding media links)
        links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if not any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.mp4']):
                links.append(href)
        
        # Extract images
        images = []
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                images.append(src)
        
        # Extract videos
        videos = []
        for video in soup.find_all('video', src=True):
            src = video.get('src')
            if src and '.mp4' in src.lower():
                videos.append(src)
        
        return text, links, images, videos

    def _parse_rfc822_date(self, date_str: str) -> datetime:
        """Convert RFC 822 date string to datetime"""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return datetime.utcnow()

    @async_retry(retries=3, delay=1.0, backoff=2.0, exceptions=(httpx.HTTPError,))
    async def _send_to_callback(self, callback_url: str, post: ParsedPost) -> None:
        """Send parsed post to callback URL"""
        try:
            # Конвертируем Pydantic модель в dict и преобразуем HttpUrl в строки
            post_data = {
                "title": post.title,
                "link": str(post.link),  # Convert HttpUrl to string
                "guid": post.guid,
                "published_at": post.published_at.isoformat(),
                "text": post.text,
                "links": [str(link) for link in post.links],  # Convert list of HttpUrl to strings
                "images": [str(image) for image in post.images],  # Convert list of HttpUrl to strings
                "videos": [str(video) for video in post.videos],  # Convert list of HttpUrl to strings
                "raw_content": post.raw_content
            }

            response = await self.http_client.post(
                url=callback_url,
                json=post_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code >= 400:
                logger.error(f"Callback request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Callback request failed: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Error sending callback request: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send callback request: {str(e)}"
            )

    async def process_post(self, post: PostWebhook) -> None:
        """Process incoming post from Huginn"""
        start_time = time.time()
        
        logger.info(
            "Processing new post from webhook",
            extra={
                "guid": post.id,
                "title": post.title,
                "link": post.url
            }
        )

        try:
            # Extract channel name from post URL
            channel_name = self._extract_channel_name(post.url)
            if not channel_name:
                logger.error(
                    "Failed to extract channel name from URL",
                    extra={"link": post.url}
                )
                raise HTTPException(status_code=400, detail="Invalid post URL")

            channel = self.repository.get_by_channel_name(channel_name)
            if not channel:
                logger.error(
                    "Channel not found",
                    extra={"channel_name": channel_name}
                )
                raise HTTPException(status_code=404, detail="Channel not found")

            if not channel.callback_url:
                logger.error(
                    "Callback URL not set for channel",
                    extra={"channel_name": channel_name}
                )
                raise HTTPException(status_code=400, detail="Callback URL not set")

            logger.info(
                "Parsing post content",
                extra={
                    "guid": post.id,
                    "channel_name": channel_name
                }
            )

            # Parse post content
            text, links, images, videos = self._parse_html_content(post.description)
            
            # Get published date
            published_at = datetime.fromisoformat(post.date_published.replace('Z', '+00:00'))
            
            logger.debug(
                "Content parsing results",
                extra={
                    "guid": post.id,
                    "text_length": len(text),
                    "links_count": len(links),
                    "images_count": len(images),
                    "videos_count": len(videos)
                }
            )
            
            # Prepare parsed post data
            parsed_post = ParsedPost(
                title=post.title,
                link=post.url,
                guid=post.id,
                published_at=published_at,
                text=text,
                links=links,
                images=images,
                videos=videos,
                channel_name=channel_name,
                raw_content=post.description
            )

            await self._send_to_callback(channel.callback_url, parsed_post)
            
            logger.info(
                "Post processing completed",
                extra={
                    "guid": post.id,
                    "processing_time": time.time() - start_time
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error processing post",
                extra={
                    "guid": post.id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error while processing post"
            ) 