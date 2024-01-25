from sqlalchemy import Column, Integer, String, Float, ForeignKey
from passlib.context import CryptContext
from sqlalchemy.orm import relationship
from app.core.database import Base, engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    balance = Column(Float, default=100.0)  # Поле баланса для пользователя
    predictions = relationship("Prediction", back_populates="user")

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.password)

    def hash_password(self, plain_password):
        self.password = pwd_context.hash(plain_password)


class Prediction(Base):
    __tablename__ = 'predictions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    result = Column(String, nullable=False)
    cost = Column(Float, default=10.0)
    user = relationship("User", back_populates="predictions")


Base.metadata.create_all(engine)
