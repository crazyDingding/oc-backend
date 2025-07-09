# utils/redis.py
import logging
import redis
import uuid
import os
from typing import Optional

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
SESSION_PREFIX = "session:"

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()  # 检查连接
except redis.exceptions.ConnectionError:
    logging.error("Redis connection failed. Please check host/port.")
    r = None  # fallback 安全处理

def create_session(user_id: int, expire_seconds: int = 3600) -> str:
    token = str(uuid.uuid4())
    if r:
        r.setex(f"{SESSION_PREFIX}{token}", expire_seconds, user_id)
    return token

def get_user_id_by_token(token: str) -> Optional[str]:
    if r:
        return r.get(f"{SESSION_PREFIX}{token}")
    return None

def get_session(token: str) -> Optional[int]:
    try:
        if not r:
            return None
        user_id = r.get(f"{SESSION_PREFIX}{token}")
        return int(user_id) if user_id else None
    except Exception as e:
        logging.error(f"[Redis] Failed to get session: {e}")
        return None

def delete_session(token: str):
    if r:
        r.delete(f"{SESSION_PREFIX}{token}")

def refresh_session(token: str, expire_seconds: int = 3600):
    if r:
        r.expire(f"{SESSION_PREFIX}{token}", expire_seconds)