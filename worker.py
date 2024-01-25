from redis import Redis
# from rq.worker import ThreadPoolWorker as Worker
from rq.worker import Worker
from rq import Queue
# from config import REDIS_URL

listen = ['high', 'default', 'low']

conn = Redis(host="127.0.0.1", port=6379, db=0)

if __name__ == '__main__':
    worker = Worker(map(Queue, listen), connection=conn)
    worker.work()
