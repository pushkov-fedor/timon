# app/services/channel_service.py
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.repositories.channel_repository import ChannelRepository
from app.schemas.channel import ChannelCreate


class ChannelService:
    def __init__(self, db: Session):
        self.repository = ChannelRepository(db)

    def create_channel(self, channel: ChannelCreate) -> Channel:
        channel_name = self._extract_channel_name_from_url(channel.channel_url)
        self._check_channel_exists(channel_name)
        
        new_channel = Channel(channel_name=channel_name)
        return self.repository.create(new_channel)

    def _extract_channel_name_from_url(self, url: str) -> str:
        parsed_url = urlparse(str(url))
        return parsed_url.path.split('/')[-1]

    def _check_channel_exists(self, channel_name: str) -> None:
        if self.repository.get_by_channel_name(channel_name):
            raise HTTPException(status_code=400, detail="Channel already exists")