# models/role.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class Role(Base):
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    user = relationship("User", back_populates="roles")
