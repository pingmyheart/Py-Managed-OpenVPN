"""Request model for deleting a client and its credentials."""

from pydantic import BaseModel


class DeleteClientRequest(BaseModel):
    """Identify the client whose credentials should be removed.

    :ivar client_name: Common name and basename of the client's PKI files.
    """
    client_name: str
