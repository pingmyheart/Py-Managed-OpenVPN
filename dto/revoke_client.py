"""Request and response models for client certificate revocation."""

from pydantic import BaseModel

from dto import BaseResponse


class RevokeClientRequest(BaseModel):
    """Identify the client whose certificate should be revoked.

    :ivar client_name: Common name and basename of the client's PKI files.
    """
    client_name: str


class RevokeClientResponse(BaseResponse):
    """Represent a client revocation result using the base code and message."""

    pass
