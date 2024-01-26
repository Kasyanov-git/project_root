from pydantic import BaseModel
from typing import List, Optional


# Схемы для пользовательского модуля

class UserCreate(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    balance: float

    token: Optional[float] = None


# Схемы для модуля аутентификации

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Схемы для модуля предсказаний

# class PredictionRequest(BaseModel):
#     model_name: str
#     model_parameters: dict
#     data: List[List[float]]
#
#
# class PredictionResponse(BaseModel):
#     result: str
#
#
# class PredictionResult(BaseModel):
#     id: int
#     result: str
#     user_id: int
#
#     class Config:
#         from_attributes = True
