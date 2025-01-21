from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    callback_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    title = Column(String(255), nullable=True)
    photo_url = Column(String(1024), nullable=True) 