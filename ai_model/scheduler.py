import datetime
import pytz
import logging
import os

from train_models import learning
from tools.tools.db_queries import get_date, get_all_id
from tools.tools.file_manager import save_status

status = {"message": "", "last_update": None}
moscow_tz = pytz.timezone("Europe/Moscow")
BASE_DIR = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
status_file = os.path.join(BASE_DIR, "status", "ai_model.json")


# проверяем дату последнего обучения
def is_fresh_models():
    # получение последней даты обновления данных
    dte_collect = get_date(from_table="information", is_end=True)
    # получение последней даты обновления моделей
    dte_learn = get_date(from_table="ai_models", is_end=True)
    # любая возникшая ошибка не позволяет проводить дальнейшее обучение, поэтому возвращаем True
    if not dte_collect:
        return True
    # если моделей нет, то обучаем
    if not dte_learn:
        return False
    # появились новые данные - модели устарели, иначе - не обучаем
    return (dte_collect - dte_learn).days < 0


# планировщик обучения моделей
def scheduled_learn():
    status["last_update"] = datetime.datetime.now(tz=moscow_tz).strftime(format="%Y-%m-%d %H:%M:%S")

    # проверяем, есть ли страны в БД (обучение не может начаться раньше сбора)
    if not get_all_id():  # get_id():
        status["message"] = "В БД отсутствуют страны"
        save_status(file_path=status_file, status=status)
        return

    # проверка на актуальность моделей
    if is_fresh_models():
        status["message"] = "Модели обучены на последних данных"
        save_status(file_path=status_file, status=status)
        return

    # в противном случае, обучаем
    message = learning()
    status["message"] = message
    save_status(file_path=status_file, status=status)
    logging.info(f"Обучение завершено. Статус: %s", status["message"])
    return
