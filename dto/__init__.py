from pydantic import BaseModel

from enumeration.response_code_enums import ResponseCodeEnums


class BaseResponse(BaseModel):
    code: int
    message: str

    @classmethod
    def from_code(cls, code_enum: ResponseCodeEnums):
        return BaseResponse(code=code_enum.code, message=code_enum.message)
