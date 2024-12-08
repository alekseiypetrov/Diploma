from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from collect_data import parse_data
from insert_data import *
import datetime
import pytz
from app.db_pool import DatabasePool
import signal

app = Flask(__name__)
scheduler_collect = BackgroundScheduler()
scheduler_clean = BackgroundScheduler()

INTERVAL_MINUTES = 5
status = {"message": "Сервис ожидает первого выполнения", "last_update": None}


# планировщик сбора данных
def scheduled_parse():
    # global status
    country = "Россия"
    # message = parse_data(country, *extract_info(country))
    try:
        message = insert_info(*parse_data(country, *extract_info(country)))
    except Exception as e:
        status["message"] = f"Ошибка при сборе данных для {country}"
        message = None
    if not (message is None):
        status["message"] = "Сбор данных выполнен успешно"
        moscow_tz = pytz.timezone("Europe/Moscow")
        status["last_update"] = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
        logging.info("Парсинг завершен. Статус: %s", status["message"])
    # if message is None:
    #     status["message"] = f"Ошибка при сборе данных для {country}"
    # else:
    #     status["message"] = "Сбор данных выполнен успешно"
    # moscow_tz = pytz.timezone("Europe/Moscow")
    # status["last_update"] = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
    # logging.info("Парсинг завершен. Статус: %s", status["message"])


# планировщик чистки данных
def scheduled_clean():
    dte_today = datetime.date.today()
    if dte_today.month != 1:
        logging.info(
            f"Очистка завершена. Статус: Обновление происходит только в 1-м месяце, а сейчас {dte_today.month}")
    else:
        country = "Россия"
        message = clean_data(country, dte_today.year)
        logging.info("Очистка завершена. Статус: %s", message)


scheduler_collect.add_job(scheduled_parse, 'interval', minutes=INTERVAL_MINUTES)
scheduler_clean.add_job(scheduled_clean, 'interval', hours=2)


@app.route('/')
def interface():
    logging.info("Запрос к странице парсера")
    return render_template('parser.html', status=status)


def initialize_services():
    """Инициализация пула соединений и планировщиков"""
    logging.info("Инициализация сервиса...")
    DatabasePool.init_pool()
    scheduler_collect.start()
    scheduler_clean.start()
    logging.info("Сервис инициализирован.")


def shutdown_services(*args):
    """Закрытие пула соединений и остановка планировщиков"""
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
        app.run(host='0.0.0.0', port=5005, debug=False)
    except Exception as e:
        logging.error("Ошибка в работе приложения: %s", e)
        shutdown_services()
