from pydantic import BaseModel

from dto import BaseResponse


class CreateClientRequest(BaseModel):
    client_country: str
    client_organization_unit: str
    client_name: str


class CreateClientResponse(BaseResponse):
    pass
