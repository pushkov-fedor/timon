from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models.channel import Channel
from app.schemas.channel import ChannelCreate, ChannelResponse

router = APIRouter()

@router.post("/", response_model=ChannelResponse)
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db_session)):
    # Извлекаем имя канала из URL
    parsed_url = urlparse(str(channel.channel_url))
    channel_username = parsed_url.path.split('/')[-1]

    # Проверяем, существует ли канал
    db_channel = db.query(Channel).filter(Channel.username == channel_username).first()
    if db_channel:
        raise HTTPException(status_code=400, detail="Channel already exists")

    # Создаем новый канал
    new_channel = Channel(username=channel_username)
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)

    return new_channel
