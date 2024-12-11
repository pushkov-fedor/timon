from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.repositories.base import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    def __init__(self, db: Session):
        super().__init__(Channel, db)

    def get_by_channel_name(self, channel_name: str) -> Channel | None:
        return self.db.query(Channel).filter(Channel.channel_name == channel_name).first()
