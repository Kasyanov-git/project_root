from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from passlib.context import CryptContext
from sqlalchemy.orm import relationship
from core.database import Base, engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    balance = Column(Float, default=100.0)
    last_login_at = Column(DateTime, nullable=True)  # Добавляем новое поле для даты последнего входа
    created_at = Column(DateTime, server_default=func.now())  # Добавляем новое поле для даты создания
    predictions = relationship("Prediction", back_populates="user")

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.password)

    def hash_password(self, plain_password):
        self.password = pwd_context.hash(plain_password)


class Prediction(Base):
    __tablename__ = 'predictions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, unique=True, nullable=True)  # Добавляем новое поле для job_id, которое будет уникально
    user_id = Column(Integer, ForeignKey('users.id'))
    result = Column(String, nullable=True)
    cost = Column(Float, default=10.0)
    created_at = Column(DateTime, server_default=func.now())  # Добавляем новое поле для даты создания
    user = relationship("User", back_populates="predictions")

# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
