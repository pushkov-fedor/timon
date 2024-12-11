from fastapi import APIRouter, Depends

from app.api.deps import get_channel_service
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.services.channel_service import ChannelService

router = APIRouter()

@router.post("/", response_model=ChannelResponse)
def create_channel(
    channel: ChannelCreate,
    channel_service: ChannelService = Depends(get_channel_service)
):
    return channel_service.create_channel(channel)
