from app.db_pool import DatabasePool
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd

"""занесение данных в БД"""
# def insert_info(dte, id_cntry, temperature, new_cases):
def insert_info(data):
    if type(data) is str:
        return data
    database = DatabasePool.get_connection()
    try:
        cursor = database.cursor()
        query = """INSERT INTO information VALUES (%s, %s, %s, %s);"""
        for line in data.values:
            cursor.execute(query, line[3:])
        # cursor.execute(query, (dte, id_cntry, temperature, new_cases,))
        database.commit()
        cursor.close()
        message = True
    except Exception:
        message = f"Возникла ошибка при занесении новых данных в БД для даты {data.iloc[0, 3]}"
    finally:
        DatabasePool.release_connection(database)
    return message


"""извлечение данных для сбора: получение id всех стран и последней даты"""


def extract_info(countries):
    database = DatabasePool.get_connection()
    # result = False
    id_countries = []
    dte = date(2020, 1, 31)
    try:
        cursor = database.cursor()

        """получение id всех стран"""
        query = """SELECT cntry_name, id_cntry FROM country ORDER BY cntry_name"""
        cursor.execute(query, )
        result = cursor.fetchall()

        """проверка на пустоту таблицы и добавление в нее стран"""
        if not result:
            for country in countries:
                insert_country(country)

        cursor.execute(query, )
        id_countries = cursor.fetchall()

        # query = """SELECT id_cntry FROM country WHERE cntry_name = %s;"""
        # for country in countries:
        #     cursor.execute(query, (country,))
        #     result = cursor.fetchone()
        #     if not result:
        #         id_cntry = insert_country(country)
        #     else:
        #         id_cntry = result[0]
        #     id_countries.append((country, id_cntry))

        """получение для всех стран общей даты, по которой будем собирать все данные"""
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
        cursor.close()
    finally:
        DatabasePool.release_connection(database)
    # if not result:
    #     return id_countries, date(2020, 1, 31)
    # else:
    #     return id_countries, result[0] + relativedelta(months=1)
    return pd.DataFrame(id_countries, columns=["country", "id"]).set_index("country"), dte


"""добавление новой страны"""


def insert_country(country):
    database = DatabasePool.get_connection()
    # result = None
    try:
        cursor = database.cursor()
        # query = """
        #             INSERT INTO country (id_cntry, cntry_name)
        #             VALUES ((SELECT COALESCE(MAX(id_cntry), 0) + 1 FROM country), %s)
        #             RETURNING id_cntry;
        #         """
        query = """
                    INSERT INTO country (id_cntry, cntry_name)
                    VALUES ((SELECT COALESCE(MAX(id_cntry), 0) + 1 FROM country), %s);
                """
        cursor.execute(query, (country,))
        # result = cursor.fetchone()[0]
        database.commit()
        cursor.close()
    finally:
        DatabasePool.release_connection(database)
    # return result


# чистка данных: перевод "старых" данных в среднегодовые показатели
def clean_data(country, year):
    database = DatabasePool.get_connection()
    flag = False
    try:
        cursor = database.cursor()
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
        WHERE c.cntry_name = %s
        ORDER BY year;
        """
        cursor.execute(query, (year, country))
        result = cursor.fetchall()
        if result:
            flag = True
            id_cntry = result[0][1]
            query = """INSERT INTO avg_year_info VALUES (%s, %s, %s, %s);"""
            for line in result:
                cursor.execute(query, line)

            query = """DELETE FROM information 
            WHERE (%s - DATE_PART('Year', dte) >= 2) AND (id_cntry = %s);"""
            cursor.execute(query, (year, id_cntry))
            database.commit()

        cursor.close()
    finally:
        DatabasePool.release_connection(database)
    if flag:
        return "Данные успешно перенесены"
    else:
        return "Нет данных для переноса"
