import uuid
import os
from app.schema.schemas import User as UserSchema, UserCreate, Token
from rq.job import Job
from app.core.worker import conn
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import create_access_token, get_current_user
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.models.models import User as UserModel
from app.utils.prediction import perform_async_prediction
from app.utils.preprocessing import read_user_data, preprocess_user_input

from app.core.config import MODEL_COSTS

UPLOAD_DIRECTORY = "./uploaded_files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


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


app = FastAPI()


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
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


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


@app.post("/predict/")
async def predict(file_id: str, model_name: str, current_user: UserModel = Depends(get_current_user),
                  db: Session = Depends(get_db)):
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
    print('predict_model: ', file_id)
    file_path = f"{UPLOAD_DIRECTORY}/{file_id}"
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Файл не найден.")

    user_data = read_user_data(file_content)
    processed_data = preprocess_user_input(user_data)

    # Выполнение асинхронного предсказания
    job_id = perform_async_prediction(model_name, processed_data)

    # Списание стоимости предсказания с баланса пользователя
    current_user.balance -= MODEL_COSTS[model_name]
    db.commit()
    db.refresh(current_user)

    return {"job_id": job_id}


@app.get("/get_prediction_status/{job_id}")
def get_prediction_status(job_id: str):
    """
    Получение статуса выполнения задачи
    :param job_id:    Идентификатор задачи
    :return:       Статус выполнения задачи
    """
    # Пытаемся получить информацию о задаче из очереди RQ
    job = Job.fetch(job_id, connection=conn)
    if job.is_finished:
        # Возвращаем результат, если задача выполнена
        return {"status": "finished", "result": job.result}
    elif job.is_failed:
        # Возвращаем статус, если выполнение задачи провалено
        return {"status": "failed"}
    else:
        # Иначе сообщаем, что задача все еще выполняется
        return {"status": "in_progress"}


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
