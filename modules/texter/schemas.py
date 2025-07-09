# modules/texter/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, Literal, Annotated


# ---------------- Dialogue Schemas ----------------

class DialogueCreate(BaseModel):
    character_id: int
    sender: Literal["user", "character"]
    content: str

class DialogueResponse(BaseModel):
    id: int
    character_id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True