"""Define the common response envelope shared by API payloads."""

from pydantic import BaseModel

from enumeration.response_code_enums import ResponseCodeEnums


class BaseResponse(BaseModel):
    """Carry an application result code and its human-readable message.

    :ivar code: Application response code, not necessarily an HTTP status.
    :ivar message: Human-readable result description.
    """
    code: int
    message: str

    @classmethod
    def from_code(cls, code_enum: ResponseCodeEnums):
        """Build a base response from a predefined result.

        :param code_enum: Enum member supplying the code and message.
        :return: A ``BaseResponse`` instance, even when called on a subclass.
        """
        return BaseResponse(code=code_enum.code, message=code_enum.message)
