# modules/character/crud.py

from sqlalchemy.orm import Session
from . import schemas
from .models import Character

# Create a new character
def create_character(db: Session, character: schemas.CharacterCreate, user_id: int, description: str):
    new_character = Character(
        user_id=user_id,
        name=character.name or "Unnamed Hero",
        description=description,  # 👈 用手动处理过的字符串字段
        status=character.status,
    )
    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    return new_character

# Get all characters belonging to a user
def get_characters_by_user(db: Session, user_id: int):
    return db.query(Character).filter(Character.user_id == user_id).all()

def get_character_by_id(db: Session, character_id: int):
    return db.query(Character).filter(Character.id == character_id).first()

def get_character_by_name(db: Session, name: str, user_id: int = None):
    query = db.query(Character).filter(Character.name == name)
    if user_id is not None:
        query = query.filter(Character.user_id == user_id)
    return query.first()

def update_character_final_image_url(db: Session, character_id: int, image_url: str):
    character = get_character_by_id(db, character_id)
    if character:
        character.final_image_url = image_url
        db.commit()
        db.refresh(character)
    return character

def update_character_generated_dialogue(db: Session, character_id: int, generated_dialogue: str):
    character = db.query(Character).filter(Character.id == character_id).first()
    if character:
        character.generated_dialogue = generated_dialogue
        db.commit()
        db.refresh(character)
    return character