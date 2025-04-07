from collect_data import parse_data
from insert_data import clean_data
import datetime
import pytz
import logging

status = {"message": "Сервис ожидает первого выполнения", "last_update": None}


# планировщик сбора данных
def scheduled_parse():
    moscow_tz = pytz.timezone("Europe/Moscow")
    status["last_update"] = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
    try:
        message = parse_data()
    except Exception as e:
        message = f"Обработано исключение при сборе данных"
    if type(message) is bool:
        status["message"] = "Сбор данных выполнен успешно"
    else:
        status["message"] = message
    logging.info("Парсинг завершен. Статус: %s", status["message"])


# планировщик чистки данных
def scheduled_clean():
    dte_today = datetime.date.today()
    message = clean_data(dte_today.year)
    status["message"] = message
    logging.info("Очистка завершена. Статус: %s", message)
