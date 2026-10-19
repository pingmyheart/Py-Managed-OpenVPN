"""Request and response models for client certificate renewal."""

from pydantic import BaseModel

from dto import BaseResponse


class RenewClientRequest(BaseModel):
    """Identify the client whose certificate should be reissued.

    :ivar client_name: Common name and basename of the client's PKI files.
    """
    client_name: str


class RenewClientResponse(BaseResponse):
    """Represent a client renewal result using the base code and message."""

    pass
