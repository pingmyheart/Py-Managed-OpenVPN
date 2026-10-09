from pydantic import BaseModel

from dto import BaseResponse


class RevokeClientRequest(BaseModel):
    client_name: str


class RevokeClientResponse(BaseResponse):
    pass
