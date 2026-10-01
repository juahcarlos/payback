from pydantic import BaseModel


class RestoreCodeQueryParams(BaseModel):
    email: str


class RestoreCodeResponse(BaseModel):
    email: str
    status: str
