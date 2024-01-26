import joblib
from models.models import Prediction
from core.database import get_db
from core.worker import app
from rq import Queue
from core.config import MODEL_COSTS

# Загрузка обученных моделей
MODELS = {
    "lr_model": joblib.load("ml_models/lr_model.joblib"),
    "gb_model": joblib.load("ml_models/gb_model.joblib"),
}


def perform_prediction(model_name: str, features: list, user_id: int):
    model = MODELS.get(model_name)
    if not model:
        raise ValueError("Model not found.")

    try:
        # Оберните вызов функции предсказания в блок try/except
        prediction_result = model.predict([features])  # Модель ожидает список списков признаков
        print("prediction_result: ", prediction_result)
        return prediction_result[0]

    except Exception as exc:
        # Залогируем исключение, и позволим Celery отметить задачу как неудачную
        print(f"Prediction failed: {exc}")
        # self.update_state(state="FAILURE", meta={'exc': str(exc)})
        raise exc


@app.task(bind=True)
def perform_async_prediction(self, model_name: str, file_content: list, user_id: int):
    """
    Функция ставит задачу на асинхронное выполнение предсказания с использованием Celery.
    .Описание.
    """
    # Добавление задачи в очередь Celery и возврат ID задачи:
    # task = perform_prediction.apply_async((model_name, file_content, user_id))
    # task =
    # print("task: ", task)
    return perform_prediction(model_name, file_content, user_id)
# def perform_async_prediction(model_name: str, file_content: list, user_id: int):
#     """
#     Функция ставит задачу на асинхронное выполнение предсказания в RQ очередь.
#     :param model_name: Название модели, которую хочет использовать пользователь.
#     :param file_content: Содержимое текстового файла, содержащего данные для предсказания.
#     :param user_id: Идентификатор пользователя.
#     :return: Идентификатор задачи в RQ.
#     """
#     queue = Queue(connection=conn)
#     # features = parse_file_content(file_content)
#     job = queue.enqueue(perform_prediction, model_name, file_content, user_id)
#     return job.get_id()
