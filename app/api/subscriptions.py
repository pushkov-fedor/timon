from fastapi import APIRouter, Depends

from app.api.deps import get_channel_service
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from app.services.channel_service import ChannelService

router = APIRouter()

@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Create a new subscription to a Telegram channel.
    If the channel is not monitored yet, it will be added automatically.
    """
    return await channel_service.create_subscription(subscription)

@router.delete("/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: int,
    channel_service: ChannelService = Depends(get_channel_service)
):
    """
    Deactivate a subscription.
    If this was the last active subscription for the channel,
    the channel monitoring will be stopped.
    """
    await channel_service.delete_subscription(subscription_id)
    return 