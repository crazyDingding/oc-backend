from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship

from database.base import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    image_type = Column(String(50), nullable=False)  # 如 avatar / generated / expression
    input_type = Column(String(20), nullable=True)
    # Optional field to clarify image source:
    #   - text_prompt: generated from text
    #   - image_prompt: generated from user-uploaded image
    #   - upload: directly uploaded by user
    # Helps trace how the image was created.
    image_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    character = relationship("Character", back_populates="images")
