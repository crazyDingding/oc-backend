from datetime import datetime

from sqlalchemy.orm import Session
from . import schemas
from . import models
from .models import Dialogue


# ---------------- Dialogue ----------------
def create_dialogue(db: Session, dialogue: schemas.DialogueCreate):
    db_dialogue = models.Dialogue(
        character_id=dialogue.character_id,
        sender=dialogue.sender,
        content=dialogue.content,
        timestamp=datetime.utcnow()
    )
    db.add(db_dialogue)
    db.commit()
    db.refresh(db_dialogue)
    return db_dialogue

def get_dialogues_by_character(db: Session, character_id: int):
    return db.query(Dialogue).filter(Dialogue.character_id == character_id).all()