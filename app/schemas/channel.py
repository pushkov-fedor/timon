from pydantic import BaseModel, ConfigDict, HttpUrl


class ChannelCreate(BaseModel):
    channel_url: HttpUrl

class ChannelResponse(BaseModel):
    id: int
    channel_name: str
    
    model_config = ConfigDict(from_attributes=True)
