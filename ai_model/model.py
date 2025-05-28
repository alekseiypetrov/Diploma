from apscheduler.schedulers.background import BackgroundScheduler
import logging
import signal
import time

from tools.tools.db_pool import DatabasePool
from scheduler import scheduled_learn

scheduler_learn = BackgroundScheduler()
scheduler_learn.add_job(scheduled_learn, 'interval', minutes=10)


def initialize_services():
    logging.info("Инициализация сервиса...")
    DatabasePool.init_pool()
    scheduler_learn.start()
    logging.info("Сервис инициализирован.")


# Закрытие пула соединений и остановка планировщиков
def shutdown_services(*args):
    logging.info("Завершение работы сервиса...")
    scheduler_learn.shutdown()
    DatabasePool.close_pool()
    logging.info("Сервис завершил работу.")
    exit(0)


if __name__ == '__main__':
    # Инициализация сервисов
    initialize_services()

    # Обработка сигнала завершения (CTRL+C или завершение процесса)
    signal.signal(signal.SIGINT, shutdown_services)
    signal.signal(signal.SIGTERM, shutdown_services)

    try:
        while True:
            time.sleep(0.1)
    except Exception as e:
        logging.error("Ошибка в работе приложения: %s", e)
    finally:
        shutdown_services()
