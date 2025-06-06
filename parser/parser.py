from apscheduler.schedulers.background import BackgroundScheduler
import logging
import signal
import time

from schedulers import scheduled_parse, scheduled_clean
from tools.tools.db_pool import DatabasePool

scheduler_collect = BackgroundScheduler()
scheduler_clean = BackgroundScheduler()

scheduler_collect.add_job(scheduled_parse, 'interval', minutes=5)
scheduler_clean.add_job(scheduled_clean, 'interval', minutes=120)


# Инициализация пула соединений и планировщиков
def initialize_services():
    logging.info("Инициализация сервиса...")
    DatabasePool.init_pool()
    scheduler_collect.start()
    scheduler_clean.start()
    logging.info("Сервис инициализирован.")


# Закрытие пула соединений и остановка планировщиков
def shutdown_services(*args):
    logging.info("Завершение работы сервиса...")
    scheduler_collect.shutdown()
    scheduler_clean.shutdown()
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
