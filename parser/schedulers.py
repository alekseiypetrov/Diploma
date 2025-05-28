from collect_data import parse_data
from insert_data import clean_data
import datetime
import pytz
import logging
import os

from tools.tools.file_manager import save_status

status = {"message": "", "last_update": None}
moscow_tz = pytz.timezone("Europe/Moscow")
BASE_DIR = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
status_file = os.path.join(BASE_DIR, "status", "parser.json")


# планировщик сбора данных
def scheduled_parse():
    status["last_update"] = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
    try:
        message = parse_data()
    except Exception as e:
        message = f"Обработано исключение при сборе данных"
    if type(message) is bool:
        status["message"] = "Сбор данных выполнен успешно"
    else:
        status["message"] = message
    save_status(file_path=status_file, status=status)
    logging.info("Парсинг завершен. Статус: %s", status["message"])


# планировщик чистки данных
def scheduled_clean():
    dte_today = datetime.date.today()
    message = clean_data(dte_today.year)
    status["message"] = message
    save_status(file_path=status_file, status=status)
    logging.info("Очистка завершена. Статус: %s", message)
