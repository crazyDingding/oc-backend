# modules/users/crud.py
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models
from . import schemas
from utils.security import hash_password, verify_password
from utils.redis import create_session, delete_session
from .models import User


# ---------------- Users ----------------
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def register_user(db: Session, user: schemas.UserCreate):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        return {"error": "Username already exists"}

    hashed_pw = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        hashed_password=hashed_pw,
        email=user.email,
        phone_number=user.phone_number,
        avatar_url=user.avatar_url,
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

def login_user(db: Session, user: schemas.UserCreate):
    db_user = get_user_by_username(db, user.username)
    if not db_user:
        return {"error": "Username not found"}
    if not verify_password(user.password, db_user.hashed_password):
        return {"error": "Incorrect password"}

    token = create_session(user_id=db_user.id)
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "role": db_user.role
        }
    }

# ✅ 修改密码
def change_password(db: Session, user_id: int, old_password: str, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"message": "Password changed successfully"}


# ✅ 登出：删除 Redis 中的会话
def logout_user(token: str):
    success = delete_session(token)
    if success:
        return {"message": "Logout successful"}
    else:
        return {"error": "Invalid token or session expired"}




