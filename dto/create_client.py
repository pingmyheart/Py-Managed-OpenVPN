"""Request and response models for client certificate creation."""

from pydantic import BaseModel

from dto import BaseResponse


class CreateClientRequest(BaseModel):
    """Describe the subject of a new client certificate.

    :ivar client_country: Country value used in the certificate subject.
    :ivar client_organization_unit: Organizational unit used in the subject.
    :ivar client_name: Common name and basename of the client's PKI files.
    """
    client_country: str
    client_organization_unit: str
    client_name: str


class CreateClientResponse(BaseResponse):
    """Represent a client creation result using the base code and message."""

    pass
