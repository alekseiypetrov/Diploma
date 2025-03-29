from train_models import learning
from app.db_pool import DatabasePool
from parser.insert_data import extract_info
from parser.collect_data import import_countries
import datetime
import pytz
import logging

log = {"status": "Сервис ожидает первого выполнения", "temp": None, "covid": None, "last_update": None}


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
        dte = result.fetchone()[0]
        flag = (current_date - dte).days() < 15
        cursor.close()
    except Exception as e:
        flag = True
    finally:
        DatabasePool.release_connection(database)
    return flag
