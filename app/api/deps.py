from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.channel_service import ChannelService


def get_db_session() -> Session:
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

def get_channel_service(db: Session = Depends(get_db_session)) -> ChannelService:
    return ChannelService(db)
