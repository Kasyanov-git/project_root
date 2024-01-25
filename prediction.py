import joblib
from models import Prediction, User
from database import get_db
from worker import conn
from rq import Queue
from config import MODEL_COSTS

# Загрузка обученных моделей
MODELS = {
    "model1": joblib.load("models/lr_model.joblib"),
    "model2": joblib.load("models/gb_model.joblib"),
}


def parse_file_content(content: str) -> list:
    """
    Функция преобразует содержимое файла пользователя в формат пригодный для классификатора.
    :param content: Содержимое текстового файла пользователя в виде строки.
    :return: Список числовых признаков, извлеченных из файла.
    """
    # здесь предполагается, что каждая строка файла содержит один вектор признаков
    features = [list(map(float, line.split())) for line in content.strip().split('\n')]
    return features


def perform_prediction(model_name: str, features: list, user_id: int):
    """
    Функция выполняет асинхронное выполнение предсказания модели.
    :param model_name:  Название модели, которую хочет использовать пользователь.
    :param features:    Список числовых признаков, извлеченных из файла.
    :param user_id:     Идентификатор пользователя.
    :return:    Идентификатор задачи в RQ.
    """
    model = MODELS.get(model_name)
    if not model:
        raise ValueError("Model not found.")

    # Выполнение предсказания
    prediction_result = model.predict(features)

    # Сохранение предсказания в базу данных
    db = next(get_db())
    prediction = Prediction(
        user_id=user_id,
        result=str(prediction_result),
        cost=MODEL_COSTS[model_name]
    )
    db.add(prediction)
    db.commit()

    return prediction_result


def perform_async_prediction(model_name: str, file_content: str):
    """
    Функция ставит задачу на асинхронное выполнение предсказания в RQ очередь.
    :param model_name: Название модели, которую хочет использовать пользователь.
    :param file_content: Содержимое текстового файла, содержащего данные для предсказания.
    :return: Идентификатор задачи в RQ.
    """
    queue = Queue(connection=conn)
    job = queue.enqueue(perform_prediction, model_name, file_content)
    return job.get_id()
