import uuid
import os
from datetime import datetime

from schema.schemas import User as UserSchema, UserCreate, Token
from core.worker import app as celery_app
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from core.auth import create_access_token, get_current_user
from core.database import get_db
from sqlalchemy.orm import Session
from models.models import User as UserModel, Prediction
from utils.prediction import perform_async_prediction, perform_prediction
from utils.preprocessing import read_user_data, preprocess_user_input

from core.config import MODEL_COSTS

UPLOAD_DIRECTORY = "./uploaded_files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

app = FastAPI()


def authenticate_user(db: Session, username: str, password: str):
    """
    Проверяет, существует ли пользователь с таким логином и паролем
    :param db:       БД
    :param username:    Логин пользователя
    :param password:    Пароль пользователя
    """
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user


@app.post("/users/register", response_model=UserSchema)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Создание нового пользователя
    :param user_data:    Данные нового пользователя
    :param db:           БД
    """
    existing_user = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    user = UserModel(username=user_data.username)
    user.hash_password(user_data.password)
    user.balance = 500
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
        Получение токена для авторизации
    :param form_data:    Форма авторизации
    :param db:          БД
    :return:       Токен
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Обновляем дату последнего входа пользователя
    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}


@app.get("/users/me/", response_model=UserSchema)
def get_current_user_info(current_user: UserModel = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе
    :param current_user:    Текущий пользователь
    """
    return current_user


@app.put("/users/update_balance", response_model=UserSchema)
def update_user_balance(amount: float, current_user: UserModel = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """
    Обновление баланса пользователя
    :param amount:    Баланс пользователя
    :param current_user:    Текущий пользователь
    :param db:             БД
    :return:       Текущий пользователь
    """
    current_user.balance += amount
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/users/{user_id}/predictions")
def get_user_predictions(user_id: int, db: Session = Depends(get_db)):
    predictions = db.query(Prediction).filter(Prediction.user_id == user_id).all()
    return predictions

@app.post("/predict/")
async def predict(file_id: str, model_name: str, current_user: UserModel = Depends(get_current_user),
                  db: Session = Depends(get_db), ):
    """
    Выполнение асинхронного предсказания
    :param file_id:    Идентификатор файла
    :param model_name:    Название модели
    :param current_user:    Текущий пользователь
    :param db:             БД
    :return:       Идентификатор задачи
    """
    # Проверка баланса пользователя и наличия модели
    if MODEL_COSTS[model_name] > current_user.balance:
        raise HTTPException(status_code=400, detail="Недостаточно кредитов.")
    # Достаем содержимое файла

    file_path = f"{UPLOAD_DIRECTORY}/{file_id}"
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Файл не найден.")

    user_data = read_user_data(file_content)
    processed_data = preprocess_user_input(user_data)

    # Выполнение асинхронного предсказания
    prediction = perform_async_prediction.apply_async((model_name, processed_data, current_user.id))
    print('perform_async_prediction: ', prediction.result)
    job_id = prediction.id
    prediction = Prediction(
        job_id=job_id,
        user_id=current_user.id,
        result=prediction.result,
        cost=MODEL_COSTS[model_name]
    )
    db.add(prediction)
    # Списание стоимости предсказания с баланса пользователя
    current_user.balance -= MODEL_COSTS[model_name]
    db.commit()
    db.refresh(current_user)

    return {"job_id": job_id}


@app.get("/get_prediction_status/{job_id}")
def get_prediction_status(job_id: str, db: Session = Depends(get_db)):
    """
    Получение статуса выполнения задачи в Celery
    .Описание.
    """
    task = celery_app.AsyncResult(job_id)
    if task.state == 'SUCCESS':
        return {"status": "finished", "result": task.result}
    elif task.state == 'FAILURE':
        return {"status": "failed", "result": str(task.result)}  # Возможно, добавить обработку ошибок
    else:
        return {"status": task.state}


@app.get("/predictions/{job_id}")
def get_prediction_result(job_id: str, db: Session = Depends(get_db)):
    """
    Получение результата предсказания по идентификатору задачи.
    :param job_id: Идентификатор задачи
    :param db: База данных
    """
    task_result = celery_app.AsyncResult(job_id)
    if task_result.ready():
        prediction = db.query(Prediction).filter(Prediction.job_id == job_id).first()
        if prediction:
            prediction.result = task_result.result
            db.commit()
            db.refresh(prediction)
            return prediction
        else:
            return "Результат не найден."
    else:
        # Задача еще не завершена
        return "Задача еще обрабатывается."


@app.post("/upload_file/")
async def upload_file(file: UploadFile = File(...)):
    """
    Загрузка файла
    :param file:    Файл
    :return:       Идентификатор файла
    """
    file_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIRECTORY}/{file_id}"
    with open(file_path, "wb") as file_object:
        file_object.write(await file.read())
    print('upload_model: ', file_id)
    return {"file_id": file_id}
