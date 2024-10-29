# models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    email = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)
    role = Column(String(50), unique=True, index=True, nullable=False)
