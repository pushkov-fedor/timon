from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    channel_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_monitored = Column(Boolean, default=True)
    huginn_rss_agent_id = Column(Integer, nullable=True)
    huginn_post_agent_id = Column(Integer, nullable=True)
