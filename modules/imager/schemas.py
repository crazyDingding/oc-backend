# modules/imager/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, Literal, Annotated



# ---------------- Image Schemas ----------------

class ImageCreate(BaseModel):
    character_id: int
    image_type: str  # e.g., avatar, expression, pose
    image_url: str
    input_type: Optional[Literal["text2img", "img2img"]] = None

class ImageResponse(BaseModel):
    id: int
    character_id: int
    image_type: str
    image_url: str
    input_type: Optional[str] = None  # ✅ 这样数据库值也能回显给前端
    created_at: datetime

    class Config:
        orm_mode = True
