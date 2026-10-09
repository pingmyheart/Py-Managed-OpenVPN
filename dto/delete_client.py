from pydantic import BaseModel


class DeleteClientRequest(BaseModel):
    client_name: str
