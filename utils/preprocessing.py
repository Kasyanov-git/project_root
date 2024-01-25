import json
from typing import Any, Dict


def read_user_data(file_content):
    # Преобразуем строку JSON в словарь Python
    user_data = json.loads(file_content)
    # print(user_data)
    return user_data


def preprocess_user_input(user_data: Dict[str, Any]) -> Any:
    """
    Предобработка данных пользователя для соответствия формату обучения модели.

    Параметры:
    user_data (Dict[str, Any]): Словарь с данными пользователя.

    Возвращает:
    Any: Отмасштабированные данные пользователя, подготовленные для модели.
    """
    # Предполагается, что все необходимые признаки находятся в ключе "features"
    features = user_data.get("features")
    if not features or len(features) != 241:
        raise ValueError("Некорректный формат данных: ожидается 241 признак.")

    processed_features = list(features.values())
    print(processed_features)
    return processed_features
