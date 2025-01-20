from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.repositories.base import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    def __init__(self, db: Session):
        super().__init__(Channel, db)

    def get(self, channel_id: int) -> Channel | None:
        """Get channel by ID"""
        return self.db.query(Channel).filter(Channel.id == channel_id).first()

    def get_by_channel_name(self, channel_name: str) -> Channel | None:
        """Get channel by channel_name"""
        return self.db.query(Channel).filter(Channel.channel_name == channel_name).first()

    def create(self, channel: Channel) -> Channel:
        """Create new channel"""
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel

    def update(self, channel: Channel) -> Channel:
        """Update channel in database"""
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel

    def delete(self, channel: Channel) -> None:
        """Delete channel from database"""
        self.db.delete(channel)
        self.db.commit()
