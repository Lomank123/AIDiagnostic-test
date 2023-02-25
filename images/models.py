from pydantic import BaseModel


class Image(BaseModel):
    id: int
    title: str
    img: str
