from dataclasses import dataclass


@dataclass
class RestoreCodeData:
    email: str
    status: str = "OK"


@dataclass
class EmailSendData:
    from_email: str
    email: str
    subject: str
    body: str
    name: str | None = None
