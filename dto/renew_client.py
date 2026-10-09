from pydantic import BaseModel

from dto import BaseResponse


class RenewClientRequest(BaseModel):
    client_name: str


class RenewClientResponse(BaseResponse):
    pass
