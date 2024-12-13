from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class ChannelCreate(BaseModel):
    channel_url: HttpUrl

class ChannelResponse(BaseModel):
    id: int
    channel_name: str
    huginn_rss_agent_id: Optional[int] = None
    huginn_post_agent_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)
