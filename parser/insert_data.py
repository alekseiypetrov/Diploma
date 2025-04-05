from app.db_pool import DatabasePool
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd


# занесение данных в БД
def insert_info(data):
    if type(data) is str:
        return data
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """INSERT INTO information VALUES (%s, %s, %s, %s);"""
        for line in data.values:
            cursor.execute(query, line[3:])
        database.commit()
        message = True
    except Exception:
        message = f"Возникла ошибка при занесении новых данных в БД для даты {data.iloc[0, 3]}"
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return message


# извлечение данных для сбора: получение id всех стран и последней даты
def extract_info(countries):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    id_countries = []
    dte = date(2020, 1, 31)
    try:
        # получение id всех стран
        query = """SELECT cntry_name, id_cntry FROM country ORDER BY cntry_name"""
        cursor.execute(query, )
        result = cursor.fetchall()

        # проверка на пустоту таблицы и добавление в нее стран
        if not result:
            for country in countries:
                insert_country(country)

        cursor.execute(query, )
        id_countries = cursor.fetchall()

        # получение для всех стран общей даты, по которой будем собирать все данные
        query = """SELECT dte 
                   FROM information 
                   WHERE id_cntry = %s
                   ORDER BY dte DESC
                   LIMIT 1; 
                """
        cursor.execute(query, (id_countries[-1][-1],))
        result = cursor.fetchone()
        if result:
            dte = result[0] + relativedelta(months=1)
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return pd.DataFrame(id_countries, columns=["country", "id"]).set_index("country"), dte


# добавление новой страны
def insert_country(country):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """
                    INSERT INTO country (id_cntry, cntry_name)
                    VALUES ((SELECT COALESCE(MAX(id_cntry), 0) + 1 FROM country), %s);
                """
        cursor.execute(query, (country,))
        database.commit()
    finally:
        cursor.close()
        DatabasePool.release_connection(database)


# чистка данных: перевод "старых" данных в среднегодовые показатели
def clean_data(year):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    flag = False
    try:
        query = """SELECT year, avg_info.id_cntry, avg_temp, avg_cases 
        FROM country c
        JOIN 
        (
            SELECT 
            DATE_PART('Year', dte) AS year, id_cntry, 
            AVG(temperature) as avg_temp, AVG(new_cases) as avg_cases
            FROM information
            WHERE (%s - DATE_PART('Year', dte) >= 2)
            GROUP BY year, id_cntry
        ) avg_info 
        ON c.id_cntry = avg_info.id_cntry
        ORDER BY (avg_info.id_cntry, year);
        """
        cursor.execute(query, (year,))
        result = cursor.fetchall()
        if result:
            flag = True
            query = """INSERT INTO avg_year_info VALUES (%s, %s, %s, %s);"""
            for line in result:
                cursor.execute(query, line)

            query = """DELETE FROM information WHERE (%s - DATE_PART('Year', dte) >= 2);"""
            cursor.execute(query, (year,))
            database.commit()
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    if flag:
        return "Данные очищены"
    else:
        return "Нет данных для чистки"
