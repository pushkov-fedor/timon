# app/api/deps.py

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.channel_service import ChannelService
from app.services.webhook_service import WebhookService


def get_db_session() -> Session:
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

def get_channel_service(db: Session = Depends(get_db_session)) -> ChannelService:
    return ChannelService(db)

async def get_webhook_service(
    db: Session = Depends(get_db_session)
) -> AsyncGenerator[WebhookService, None]:
    async with WebhookService(db) as service:
        yield service

def get_subscription_repository(db: Session = Depends(get_db)) -> SubscriptionRepository:
    return SubscriptionRepository(db)
