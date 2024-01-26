# from redis import Redis
# from rq import Queue, Worker
#
# listen = ['high', 'default', 'low']
#
# conn = Redis(host="127.0.0.1", port=6379, db=0)
#
# if __name__ == '__main__':
#     worker = Worker(map(Queue, listen), connection=conn)
#     worker.work()

from celery import Celery

# Создание экземпляра приложения Celery и установка брокера
app = Celery('worker',
             broker='redis://localhost:6379',  # здесь можно указать конкретную базу данных внутри Redis, если нужно
             backend='redis://localhost:6379',  # то же самое для бэкенда
             include=['utils.prediction'])  # здесь должен быть путь до файла, который содержит задачи Celery

app.conf.update(
    timezone='Europe/Moscow',
    result_expires=3600,  # Время жизни результата задачи в секундах
    worker_prefetch_multiplier=1,  # Количество дополнительных задач внутреннего запаса, которые worker подгружает одновременно
    task_track_started=True,
)

if __name__ == '__main__':
    app.start()