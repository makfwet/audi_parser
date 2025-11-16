from datetime import datetime

from pydantic import BaseModel


class PartsLinksObject(BaseModel):
    link: str
    is_parsed: int

class PartsLinksDTO(PartsLinksObject):
    id: int

class AudiPartsLightObject(BaseModel):
    data: str

class AudiPartsLightDTO(AudiPartsLightObject):
    id: int

class AudiPartsFullObject(BaseModel):
    part_code: str
    title: str | None
    quantity: str | None
    information: str | None
    link: str | None

class AudiPartsFullDTO(AudiPartsFullObject):
    id: int
    created_at: datetime