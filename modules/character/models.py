# modules/character/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base
from modules.imager.models import Image
from modules.texter import Dialogue


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    # 用户输入内容
    description = Column(Text, nullable=True)  # User input description (used in text-to-image and LLM modules)

    # 生成结果
    final_image_url = Column(String(255), nullable=True)  # Cached final generated image URL (from images table)
    generated_dialogue = Column(Text,nullable=True)  # Cached generated character description (from dialogues or LLM output)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # 关系
    owner = relationship("User", back_populates="characters")
    dialogues = relationship(Dialogue, back_populates="character")
    images = relationship(Image, back_populates="character")