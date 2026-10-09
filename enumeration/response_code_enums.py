from enum import Enum
from http import HTTPStatus


class ResponseCodeEnums(Enum):
    """
    Enum for the response codes.
    """
    SUCCESS = (0, "Success", HTTPStatus.OK)
    INTERNAL_ERROR = (500, "Internal Server Error", HTTPStatus.INTERNAL_SERVER_ERROR)

    CLIENT_ALREADY_EXISTS = (1001, "Client already exists", HTTPStatus.CONFLICT)
    REQUESTED_FILE_NOT_FOUND = (1002, "Requested file not found", HTTPStatus.NOT_FOUND)

    def __init__(self, code: int,
                 message: str,
                 http_status_code: HTTPStatus):
        self.code = code
        self.message = message
        self.http_status_code = http_status_code

    @classmethod
    def get_by_code(cls, code: int):
        """Return the enum member by its code, or None if not found."""
        for member in cls:
            if member.code == code:
                return member
        return None
