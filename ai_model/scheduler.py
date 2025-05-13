import datetime
import pytz
import logging

from train_models import learning
from tools.tools.db_queries import get_date, get_all_id

log = {"status": "Сервис ожидает первого выполнения", "last_update": None}


# проверяем дату последнего обучения
def is_fresh_models():
    # получение последней даты обновления данных
    dte_collect = get_date(from_table="information", is_end=True)
    # получение последней даты обновления моделей
    dte_learn = get_date(from_table="ai_models", is_end=True)
    # любая возникшая ошибка не позволяет проводить дальнейшее обучение, поэтому возвращаем True
    if not dte_collect or not dte_learn:
        return True
    # появились новые данные - модели устарели, иначе - не обучаем
    return (dte_collect - dte_learn).days < 0


# планировщик обучения моделей
def scheduled_learn():
    moscow_tz = pytz.timezone("Europe/Moscow")
    log["last_update"] = datetime.datetime.now(tz=moscow_tz).strftime(format="%Y-%m-%d %H:%M:%S")

    # проверяем, есть ли страны в БД (обучение не может начаться раньше сбора)
    if not get_all_id():  # get_id():
        log["status"] = "В БД отсутствуют страны"
        return

    # проверка на актуальность моделей
    if is_fresh_models():
        log["status"] = "Модели обучены на последних данных"
        return

    # в противном случае, обучаем
    status = learning()
    log["status"] = status
    logging.info(f"Обучение завершено. Статус: %s", log["status"])
    return
