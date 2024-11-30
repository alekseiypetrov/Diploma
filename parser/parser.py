from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from collect_data import parse_data
import datetime
import pytz

INTERVAL_MINUTES = 5
status = {"message": "Сервис ожидает первого выполнения", "last_update": None}

app = Flask(__name__)
scheduler = BackgroundScheduler()


# планировщик задач
def scheduled_parse():
    global status
    country = "Россия"
    message = parse_data(country=country)
    if message is None:
        status["message"] = f"Ошибка при сборе данных для {country}"
    else:
        status["message"] = "Сбор данных выполнен успешно"
    moscow_tz = pytz.timezone("Europe/Moscow")
    status["last_update"] = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
    logging.info("Парсинг завершен. Статус: %s", status["message"])


scheduler.add_job(scheduled_parse, 'interval', minutes=INTERVAL_MINUTES)


@app.route('/')
def interface():
    logging.info("Запрос к странице парсера")
    return render_template('parser.html', status=status)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    scheduler.start()
    app.run(host='0.0.0.0', port=5005, debug=False)
