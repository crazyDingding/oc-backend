# modules/character/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Literal, Union, Dict, List, Any
from datetime import datetime

# ---------------- Character Schemas ----------------

class CharacterCreate(BaseModel):
    name: Optional[str] = None  # Optional name; backend can provide default
    description: Optional[Any] = None  # User text input
    status: Optional[Literal["active", "inactive"]] = "active"

class CharacterResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    final_image_url: Optional[str]
    generated_dialogue: Optional[str]
    created_at: datetime
    status: str

    class Config:
        orm_mode = True