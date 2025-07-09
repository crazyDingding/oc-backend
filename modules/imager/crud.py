from sqlalchemy.orm import Session
from . import schemas
from . import models
from .models import Image


# ---------------- Image ----------------
def create_image(db: Session, image: schemas.ImageCreate):
    new_image = Image(**image.dict())
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image

def get_images_by_character(db: Session, character_id: int):
    return db.query(Image).filter(Image.character_id == character_id).all()

def get_images_by_character_id(db: Session, character_id: int):
    return db.query(Image).filter(Image.character_id == character_id).all()