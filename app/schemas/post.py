# app/schemas/post.py

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class PostWebhook(BaseModel):
    """Schema for incoming webhook data from Huginn"""
    id: str
    url: str
    title: str
    description: str
    content: str
    date_published: str  # This is what Huginn sends
    last_updated: str

    @property
    def guid(self) -> str:
        """Alias for id to maintain compatibility"""
        return self.id

    @property
    def published(self) -> str:
        """Alias for date_published to maintain compatibility"""
        return self.date_published

class ParsedPost(BaseModel):
    """Schema for parsed post data to be sent to callback URL"""
    title: str
    link: str  # Changed from HttpUrl to str for flexibility
    guid: str
    published_at: datetime
    text: str
    links: List[str]
    images: List[str]
    videos: List[str]
    channel_name: str
    raw_content: str = Field(description="Original HTML content of the post")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Sample post",
                "link": "https://t.me/channel/123",
                "guid": "https://t.me/channel/123",
                "published_at": "2024-12-26T13:00:26+00:00",
                "text": "Plain text content",
                "links": ["https://example.com"],
                "images": ["https://example.com/image.jpg"],
                "videos": [],
                "channel_name": "channel",
                "raw_content": "<p>Original HTML content</p>"
            }
        } 