from celery import Celery, shared_task

@shared_task
def add(x, y):
    z = x + y
    print(z)