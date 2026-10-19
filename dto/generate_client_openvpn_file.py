"""Response model for an embedded OpenVPN client profile."""

from dto import BaseResponse


class GenerateClientOpenvpnFileResponse(BaseResponse):
    """Carry a client profile alongside the inherited result code and message.

    :ivar file_data: Single-line base64 encoding of the UTF-8 OpenVPN profile,
        including the client's private key and TLS control-channel key.
    """
    file_data: str
