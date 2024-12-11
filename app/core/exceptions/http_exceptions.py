from fastapi import HTTPException


class ChannelAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Channel already exists")

class ChannelNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Channel not found")
