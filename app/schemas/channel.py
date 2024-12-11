from pydantic import BaseModel, ConfigDict, HttpUrl


class ChannelCreate(BaseModel):
    channel_url: HttpUrl

class ChannelResponse(BaseModel):
    id: int
    username: str
    
    model_config = ConfigDict(from_attributes=True)
