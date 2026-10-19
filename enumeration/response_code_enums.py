"""Map application result codes to messages and HTTP response statuses."""

from enum import Enum
from http import HTTPStatus


class ResponseCodeEnums(Enum):
    """Define the supported API outcomes and their HTTP mappings.

    :ivar code: Numeric application result code.
    :ivar message: Human-readable description of the result.
    :ivar http_status_code: HTTP status used by controllers for this result.
    """
    SUCCESS = (0, "Success", HTTPStatus.OK)
    INTERNAL_ERROR = (500, "Internal Server Error", HTTPStatus.INTERNAL_SERVER_ERROR)

    CLIENT_ALREADY_EXISTS = (1001, "Client already exists", HTTPStatus.CONFLICT)
    REQUESTED_FILE_NOT_FOUND = (1002, "Requested file not found", HTTPStatus.NOT_FOUND)

    def __init__(self, code: int,
                 message: str,
                 http_status_code: HTTPStatus):
        """Store the application outcome and its HTTP representation.

        :param code: Application result code.
        :param message: Human-readable result description.
        :param http_status_code: HTTP status returned for this outcome.
        """
        self.code = code
        self.message = message
        self.http_status_code = http_status_code

    @classmethod
    def get_by_code(cls, code: int):
        """Look up an outcome by its application result code.

        :param code: Numeric application code to find.
        :return: Matching enum member, or ``None`` for an unknown code.
        """
        for member in cls:
            if member.code == code:
                return member
        return None
