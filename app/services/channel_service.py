# app/services/channel_service.py
import logging
from urllib.parse import urlparse

from fastapi import HTTPException
from httpx import AsyncClient, TimeoutException
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.subscription import Subscription
from app.repositories.channel_repository import ChannelRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.channel import ChannelCreate
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from app.services.huginn_client import HuginnClient

logger = logging.getLogger(__name__)


class ChannelService:
    def __init__(self, db: Session):
        self.channel_repository = ChannelRepository(db)
        self.subscription_repository = SubscriptionRepository(db)
        self.huginn_client = HuginnClient()
        self.http_client = AsyncClient(timeout=10.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    def create_channel(self, channel: ChannelCreate) -> Channel:
        channel_name = self._extract_channel_name_from_url(channel.channel_url)
        self._check_channel_exists(channel_name)
        
        new_channel = Channel(
            channel_name=channel_name,
            callback_url=str(channel.callback_url),
            is_monitored=True
        )
        
        # Проверка наличия callback_url
        if not new_channel.callback_url:
            raise HTTPException(
                status_code=400,
                detail="callback_url is required"
            )
        
        self.channel_repository.create(new_channel)
        
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
            self.channel_repository.update(new_channel)
        except HTTPException as e:
            self.channel_repository.delete(new_channel)
            raise e
        
        return new_channel

    def _extract_channel_name_from_url(self, url: str) -> str:
        parsed_url = urlparse(str(url))
        return parsed_url.path.strip('/').split('/')[-1]

    def _check_channel_exists(self, channel_name: str) -> None:
        if self.channel_repository.get_by_channel_name(channel_name):
            raise HTTPException(status_code=400, detail="Channel already exists")

    def delete_channel(self, channel_id: int) -> None:
        channel = self.channel_repository.get_by_id(channel_id)
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
        
        self.channel_repository.delete(channel)

    async def _check_channel_availability(self, channel_name: str) -> None:
        """Проверяет доступность канала через RSSHub напрямую"""
        rsshub_url = f"http://rsshub:1200/telegram/channel/{channel_name}"
        
        try:
            response = await self.http_client.get(rsshub_url)
            
            if response.status_code == 503:
                error_message = "Channel is private or inaccessible"
                if "Unable to fetch message feed" in response.text:
                    error_message = "This channel is private or doesn't exist"
                raise HTTPException(
                    status_code=400,
                    detail=error_message
                )
                
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to verify channel: HTTP {response.status_code}"
                )
                
        except TimeoutException:
            raise HTTPException(
                status_code=400,
                detail="Timeout while checking channel availability"
            )
        except Exception as e:
            logger.error(
                "Error checking channel availability",
                extra={
                    "channel_name": channel_name,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=400,
                detail="Failed to verify channel accessibility"
            )

    async def create_subscription(
        self, 
        subscription: SubscriptionCreate
    ) -> SubscriptionResponse:
        logger.info(
            "Creating subscription",
            extra={
                "channel_url": str(subscription.channel_url),
                "callback_url": str(subscription.callback_url)
            }
        )
        
        channel_name = self._extract_channel_name_from_url(subscription.channel_url)
        logger.debug(f"Extracted channel name: {channel_name}")
        
        # Проверяем доступность канала до создания чего-либо
        await self._check_channel_availability(channel_name)
        
        # Если канал доступен, продолжаем создание подписки
        channel = self.channel_repository.get_by_channel_name(channel_name)
        
        if not channel:
            logger.info(f"Channel {channel_name} not found, creating new")
            channel = Channel(
                channel_name=channel_name,
                is_monitored=True
            )
            self.channel_repository.create(channel)
            
            try:
                logger.info(f"Creating Huginn agents for channel {channel_name}")
                rss_agent_id = self.huginn_client.create_rss_agent(channel_name)
                post_agent_id = self.huginn_client.create_post_agent(channel_name)
                
                # Проверяем доступность канала
                try:
                    logger.info("Testing RSS agent connectivity")
                    status = self.huginn_client.get_agent_status(rss_agent_id)
                    if "error" in status and "503" in str(status["error"]):
                        logger.error(
                            "Channel appears to be private or inaccessible",
                            extra={"channel_name": channel_name}
                        )
                        # Удаляем созданные агенты
                        self.huginn_client.delete_agent(rss_agent_id)
                        self.huginn_client.delete_agent(post_agent_id)
                        
                        # Удаляем канал
                        self.channel_repository.delete(channel)
                        
                        raise HTTPException(
                            status_code=400,
                            detail="Channel is private or inaccessible"
                        )
                except Exception as e:
                    logger.error(
                        "Error checking channel accessibility",
                        extra={
                            "channel_name": channel_name,
                            "error": str(e)
                        }
                    )
                    # Удаляем созданные агенты и канал
                    self.huginn_client.delete_agent(rss_agent_id)
                    self.huginn_client.delete_agent(post_agent_id)
                    self.channel_repository.delete(channel)
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to verify channel accessibility"
                    )

                # Продолжаем только если канал доступен
                logger.info("Linking Huginn agents")
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
                
                channel.huginn_rss_agent_id = rss_agent_id
                channel.huginn_post_agent_id = post_agent_id
                self.channel_repository.update(channel)
                logger.info("Successfully created and linked Huginn agents")
                
            except Exception as e:
                logger.error(
                    f"Failed to create Huginn agents for channel {channel_name}",
                    exc_info=True
                )
                self.channel_repository.delete(channel)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create Huginn agents: {str(e)}"
                )
        
        # Check if subscription already exists
        existing_sub = self.subscription_repository.get_by_channel_and_callback(
            channel.id,
            str(subscription.callback_url)
        )
        
        if existing_sub:
            if existing_sub.is_active:
                logger.warning(
                    "Subscription already exists and is active",
                    extra={
                        "channel_name": channel_name,
                        "subscription_id": existing_sub.id
                    }
                )
                raise HTTPException(
                    status_code=400,
                    detail="Subscription already exists"
                )
            
            logger.info(
                "Reactivating existing subscription",
                extra={
                    "channel_name": channel_name,
                    "subscription_id": existing_sub.id
                }
            )
            existing_sub.is_active = True
            self.subscription_repository.update(existing_sub)
            return SubscriptionResponse.model_validate(existing_sub)
        
        # Create new subscription
        logger.info(
            "Creating new subscription",
            extra={
                "channel_name": channel_name,
                "channel_id": channel.id
            }
        )
        new_sub = Subscription(
            channel_id=channel.id,
            callback_url=str(subscription.callback_url),
            is_active=True
        )
        self.subscription_repository.create(new_sub)
        
        logger.info(
            "Successfully created subscription",
            extra={
                "subscription_id": new_sub.id,
                "channel_name": channel_name
            }
        )
        return SubscriptionResponse.model_validate(new_sub)

    async def delete_subscription(self, subscription_id: int) -> None:
        """Delete subscription and cleanup if needed"""
        logger.info(f"Deleting subscription {subscription_id}")
        
        subscription = self.subscription_repository.get(subscription_id)
        if not subscription:
            logger.warning(f"Subscription {subscription_id} not found")
            raise HTTPException(status_code=404, detail="Subscription not found")

        try:
            # Получаем канал до удаления подписки
            channel = self.channel_repository.get(subscription.channel_id)
            if not channel:
                logger.warning(f"Channel {subscription.channel_id} not found")
                raise HTTPException(status_code=404, detail="Channel not found")

            # Проверяем, есть ли еще активные подписки на этот канал
            active_subscriptions = self.subscription_repository.get_active_by_channel_id(
                subscription.channel_id
            )
            
            # Если это единственная активная подписка (текущая)
            if len(active_subscriptions) <= 1:
                logger.info(f"Last active subscription for channel {subscription.channel_id}, cleaning up")
                
                # Удаляем агентов в Huginn если они есть
                if channel.huginn_rss_agent_id and channel.huginn_post_agent_id:
                    logger.info("Deleting Huginn agents")
                    try:
                        self.huginn_client.delete_agent(channel.huginn_rss_agent_id)
                        self.huginn_client.delete_agent(channel.huginn_post_agent_id)
                    except Exception as e:
                        logger.error(f"Failed to delete Huginn agents: {e}")

                # Удаляем канал
                logger.info(f"Deleting channel {channel.id}")
                self.channel_repository.delete(channel)

            # Физически удаляем подписку
            self.subscription_repository.delete(subscription)
            logger.info(f"Successfully deleted subscription {subscription_id}")

        except Exception as e:
            logger.error(f"Error deleting subscription {subscription_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete subscription: {str(e)}"
            )