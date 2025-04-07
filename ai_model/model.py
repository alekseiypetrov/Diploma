from flask import Flask, Blueprint, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import signal

from app.db_pool import DatabasePool
from scheduler import scheduled_learn, log

# ai_bp = Blueprint('ai', __name__, url_prefix='/ai')
app = Flask(__name__)
scheduler_learn = BackgroundScheduler()
scheduler_learn.add_job(scheduled_learn, 'interval', minutes=15)


@app.route('/')
def interface():
    logging.info("Запрос к странице ИИ-модели")
    return render_template("ai_page.html", log=log)


# app.register_blueprint(ai_bp)

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
        app.run(host='0.0.0.0', port=5002)
    except Exception as e:
        logging.error("Ошибка в работе приложения: %s", e)
    finally:
        shutdown_services()
