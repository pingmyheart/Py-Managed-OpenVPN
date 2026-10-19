"""Response model for entries extracted from the OpenVPN routing table."""

from typing import List

from dto import BaseResponse


class ObtainConnectedClientResponse(BaseResponse):
    """Carry routing entries alongside the inherited result code and message.

    :ivar connected_clients: List of dictionaries from the status log's routing
        table, with lowercase, underscore-separated keys and string values.
    """
    connected_clients: List
