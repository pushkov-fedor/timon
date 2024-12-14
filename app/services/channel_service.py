# app/services/channel_service.py
import logging
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.repositories.channel_repository import ChannelRepository
from app.schemas.channel import ChannelCreate
from app.services.huginn_client import HuginnClient

logger = logging.getLogger(__name__)


class ChannelService:
    def __init__(self, db: Session):
        self.repository = ChannelRepository(db)
        self.huginn_client = HuginnClient()

    def create_channel(self, channel: ChannelCreate) -> Channel:
        channel_name = self._extract_channel_name_from_url(channel.channel_url)
        self._check_channel_exists(channel_name)
        
        new_channel = Channel(channel_name=channel_name)
        self.repository.create(new_channel)
        
        try:
            # Create agents
            rss_agent_id = self.huginn_client.create_rss_agent(channel_name)
            post_agent_id = self.huginn_client.create_post_agent(channel_name)
            
            # Link agents
            self.huginn_client.link_agents(rss_agent_id, post_agent_id)
            
            # Check links
            links = self.huginn_client.get_agent_links(rss_agent_id)
            logger.info(f"RSS Agent links: {links}")
            
            # RSS agent should send events to Post agent
            if post_agent_id not in links["receivers"]:
                logger.warning(f"Post agent {post_agent_id} not found in RSS agent receivers!")
            
            # Post agent should receive events from RSS
            post_links = self.huginn_client.get_agent_links(post_agent_id)
            if rss_agent_id not in post_links["sources"]:
                logger.warning(f"RSS agent {rss_agent_id} not found in Post agent sources!")
            
            # Start agents
            self.huginn_client.start_agent(rss_agent_id)
            
            # Check status
            rss_status = self.huginn_client.get_agent_status(rss_agent_id)
            post_status = self.huginn_client.get_agent_status(post_agent_id)
            
            logger.info(f"RSS Agent status: {rss_status}")
            logger.info(f"Post Agent status: {post_status}")
            
            new_channel.huginn_rss_agent_id = rss_agent_id
            new_channel.huginn_post_agent_id = post_agent_id
            self.repository.update(new_channel)
        except HTTPException as e:
            self.repository.delete(new_channel)
            raise e
        
        return new_channel

    def _extract_channel_name_from_url(self, url: str) -> str:
        parsed_url = urlparse(str(url))
        return parsed_url.path.strip('/').split('/')[-1]

    def _check_channel_exists(self, channel_name: str) -> None:
        if self.repository.get_by_channel_name(channel_name):
            raise HTTPException(status_code=400, detail="Channel already exists")

    def delete_channel(self, channel_id: int) -> None:
        channel = self.repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        try:
            if channel.huginn_rss_agent_id:
                self.huginn_client.delete_agent(channel.huginn_rss_agent_id)
            if channel.huginn_post_agent_id:
                self.huginn_client.delete_agent(channel.huginn_post_agent_id)
        except HTTPException as e:
            logger.error(f"Error deleting Huginn agents: {e}")
            raise e
        
        self.repository.delete(channel)