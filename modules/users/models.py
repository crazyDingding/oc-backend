# modules/users/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.orm import relationship

from database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)  # 邮箱可选
    phone_number = Column(String(20), unique=True, index=True, nullable=True)  # 手机号可选
    hashed_password = Column(String(128), nullable=False)

    role = Column(String(20), default="user", nullable=False)  # 用户角色，例如 admin / user
    avatar_url = Column(String(255), nullable=True)  # 头像链接
    created_at = Column(DateTime, default=datetime.utcnow)  # 注册时间
    is_active = Column(Boolean, default=True)  # 是否启用

    # ✅ 与 Character 关联（1对多）
    characters = relationship("Character", back_populates="owner")
# TODO: 邮箱/手机号注册,添加用户角色权限, 添加头像/创建时间等信息





