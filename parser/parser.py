from flask import Flask, Blueprint, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import signal

from schedulers import scheduled_parse, scheduled_clean, status
from app.db_pool import DatabasePool

# parser_bp = Blueprint('parser', __name__, url_prefix='/parser')
app = Flask(__name__)
scheduler_collect = BackgroundScheduler()
scheduler_clean = BackgroundScheduler()

scheduler_collect.add_job(scheduled_parse, 'interval', minutes=5)
scheduler_clean.add_job(scheduled_clean, 'interval', minutes=120)


@app.route('/')
def interface():
    logging.info("Запрос к странице парсера")
    return render_template('parser_page.html', status=status)


# app.register_blueprint(parser_bp)


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
        app.run(host='0.0.0.0', port=5001)
    except Exception as e:
        logging.error("Ошибка в работе приложения: %s", e)
    finally:
        shutdown_services()
