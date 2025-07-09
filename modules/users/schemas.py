# modules/users/schemas.py
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal, Annotated
from datetime import datetime

# ---------------- User Schemas ----------------
class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=14)]
    password: Annotated[str, Field(min_length=6, max_length=18)]

    @field_validator('username')
    @classmethod
    def username_length_and_charset(cls, v):
        # 中文字符算两个长度
        if sum(2 if '\u4e00' <= ch <= '\u9fff' else 1 for ch in v) > 14:
            raise ValueError("Username cannot exceed 14 English characters or 7 Chinese characters.")
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if ' ' in v:
            raise ValueError("Password cannot contain spaces.")
        if re.search(r'[\u4e00-\u9fff]', v):
            raise ValueError("Password cannot contain Chinese characters.")
    #
    #     categories = 0
    #     if re.search(r'[a-zA-Z]', v): categories += 1
    #     if re.search(r'\d', v): categories += 1
    #     if re.search(r'\W', v): categories += 1  # 非字母数字
    #
    #     if categories < 2:
    #         raise ValueError("Password must contain at least two types: letters, numbers, or symbols.")
        return v
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[Literal["user", "admin"]] = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    phone_number: Optional[str]
    avatar_url: Optional[str]
    role: str
    created_at: datetime

    class Config:
        orm_mode = True

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=18)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if ' ' in v:
            raise ValueError("New password cannot contain spaces.")
        if re.search(r'[\u4e00-\u9fff]', v):
            raise ValueError("New password cannot contain Chinese characters.")
        # categories = 0
        # if re.search(r'[a-zA-Z]', v): categories += 1
        # if re.search(r'\d', v): categories += 1
        # if re.search(r'\W', v): categories += 1
        # if categories < 2:
        #     raise ValueError("New password must contain at least two types: letters, numbers, or symbols.")
        return v



