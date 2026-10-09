from typing import List

from dto import BaseResponse


class ObtainConnectedClientResponse(BaseResponse):
    connected_clients: List
