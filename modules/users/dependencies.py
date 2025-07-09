# modules/users/dependencies.py
from database.database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends, Header, HTTPException
from utils.redis import get_user_id_by_token, refresh_session
from .models import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
        token: str = Header(...),
        db: Session = Depends(get_db)
) -> User:
    user_id = get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    refresh_session(token)  # ✅ 自动刷新 TTL

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user