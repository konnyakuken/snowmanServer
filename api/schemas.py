from typing import List, Optional
from pydantic import BaseModel

class ItemBase(BaseModel):
    title: str


class CreatePhoto(ItemBase):
    id: int
    class Config:
        orm_mode = True
