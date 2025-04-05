from train_models import learning
from app.db_pool import DatabasePool
import datetime
import pytz
import logging

log = {"status": "Сервис ожидает первого выполнения", "temp": None, "covid": None, "last_update": None}


# планировщик обучения моделей
def scheduled_learn():
    moscow_tz = pytz.timezone("Europe/Moscow")
    log["last_update"] = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
    log["temp"] = None
    log["covid"] = None
    # проверка на актуальность моделей
    if is_fresh_models():
        log["status"] = "Модели обучены на последних данных"
        return
    id_countries = get_id()
    # проверяем, есть ли страны в БД (обучение не может начаться раньше сбора)
    if not id_countries:
        log["status"] = "В БД отсутствуют страны"
        return
    # в противном случае, обучаем
    result = learning(id_countries)
    log["status"] = result["status"]
    log["temp"] = result["temp"]
    log["covid"] = result["covid"]
    logging.info(f"Обучение завершено. Статус: %s", log["status"])
    return


# извлечение данных для сбора: получение id всех стран и последней даты
def get_id():
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    id_countries = []
    try:
        # получение id всех стран
        query = """SELECT id_cntry FROM country;"""
        cursor.execute(query, )
        id_countries = cursor.fetchall()
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return id_countries


# проверяем дату последнего обучения
def is_fresh_models():
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        # получение последней даты обновления данных
        query = """SELECT dte FROM information 
        ORDER BY dte DESC
        LIMIT 1;
        """
        cursor.execute(query, )
        result = cursor.fetchone()
        if not result:
            return True
        dte_collect = result[0]

        # получение последней даты обновления моделей
        query = """SELECT dte FROM ai_models
        ORDER BY dte DESC
        LIMIT 1;
        """
        cursor.execute(query, )
        result = cursor.fetchone()
        if not result:
            return False
        dte_learn = result[0]
        # появились новые данные - модели устарели, иначе - не обучаем
        return (dte_collect - dte_learn).days < 0
    # любая возникшая ошибка не позволяет проводить дальнейшее обучение, поэтому возвращаем True
    except Exception as e:
        return True
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
