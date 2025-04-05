from train_models import learning
from app.db_pool import DatabasePool
import datetime
from datetime import date
import pytz
import logging
import pandas as pd
import os

log = {"status": "Сервис ожидает первого выполнения", "temp": None, "covid": None, "last_update": None}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def import_countries():
    file_path = os.path.join(BASE_DIR, "parser", "links", "temperature sources.json")
    return pd.read_json(file_path)


# извлечение данных для сбора: получение id всех стран и последней даты
def extract_info(countries):
    database = DatabasePool.get_connection()
    id_countries = []
    dte = date(2020, 1, 31)
    try:
        cursor = database.cursor()

        # получение id всех стран
        query = """SELECT cntry_name, id_cntry FROM country ORDER BY cntry_name"""
        cursor.execute(query, )
        result = cursor.fetchall()

        cursor.execute(query, )
        id_countries = cursor.fetchall()

        query = """SELECT dte 
                   FROM information 
                   WHERE id_cntry = %s
                   ORDER BY dte DESC
                   LIMIT 1; 
                """
        cursor.execute(query, (id_countries[-1][-1],))
        result = cursor.fetchone()
        if result:
            dte = result[0]
        cursor.close()
    finally:
        DatabasePool.release_connection(database)
    return pd.DataFrame(id_countries, columns=["country", "id"]).set_index("country"), dte


# планировщик обучения моделей
def scheduled_learn():
    # проверяем, как давно обновлялись данные
    countries, last_date = extract_info(tuple(sorted(import_countries().country.values)))
    countries = countries.reset_index()
    current_date = datetime.datetime.today()
    moscow_tz = pytz.timezone("Europe/Moscow")
    log["last_update"] = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
    log["temp"] = None
    log["covid"] = None
    if (current_date - last_date).days > 31:
        log["status"] = "В БД отсутствуют новые данные"
        return
    # проверяем, как давно обучалась модель
    if fresh_models(current_date):
        log["status"] = "Модели обучены на последних данных"
        return
    # в противном случае, обучаем
    result = learning(countries)
    log["status"] = result["status"]
    log["temp"] = result["temp"]
    log["covid"] = result["covid"]
    logging.info("Обучение завершено. Статус: %s", log["status"])
    return


# проверяем дату последнего обучения
def fresh_models(current_date):
    database = DatabasePool.get_connection()
    try:
        cursor = database.cursor()
        query = """SELECT dte FROM ai_models
        ORDER BY dte DESC
        LIMIT 1;
        """
        result = cursor.execute(query, )
        if not result:
            flag = False
        else:
            dte = result.fetchone()[0]
            flag = (current_date - dte).days() < 15
        cursor.close()
    except Exception as e:
        flag = True
    finally:
        DatabasePool.release_connection(database)
    return flag
