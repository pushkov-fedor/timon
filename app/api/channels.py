from fastapi import APIRouter, Depends, HTTPException

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

@router.delete("/{channel_id}", status_code=204)
def delete_channel(
    channel_id: int,
    channel_service: ChannelService = Depends(get_channel_service)
):
    channel_service.delete_channel(channel_id)
    return
