# database/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from database.base import Base  # ✅ 从 base.py 获取 Base
from modules.users.models import User
from modules.character.models import Character
from modules.texter.models import Dialogue
from modules.imager.models import Image

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv('DATABASEIPV4')
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)