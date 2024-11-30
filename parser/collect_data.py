import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta
import psycopg2
from app.config import Config
import logging

DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI


# занесение данных в БД
def insert_info(dte, id_cntry, temperature, new_cases):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    try:
        query = """INSERT INTO information VALUES (%s, %s, %s, %s);"""
        cursor.execute(query, (dte, id_cntry, temperature, new_cases,))
        conn.commit()
        message = True
    except Exception:
        message = None
    finally:
        cursor.close()
        conn.close()
    return message


# сбор данных о заболеваемости
def parse_covid_data(response, dte, country):
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('a', class_='btn btn-primary btn-sm')
    file_url = quotes[0]['href']

    covid_dataset = (pd.read_csv(file_url).
                     drop(['Country_code', 'WHO_region', 'Cumulative_cases', 'New_deaths', 'Cumulative_deaths'],
                          axis=1).
                     set_index("Date_reported"))

    covid_dataset = covid_dataset[covid_dataset['Country'] == country]
    covid_dataset = covid_dataset.drop(columns=['Country'])
    covid_dataset.index = pd.to_datetime(covid_dataset.index)
    covid_dataset['New_cases'] = covid_dataset['New_cases'].fillna(0)
    covid_dataset = covid_dataset.resample('ME').sum()

    cur_dte = pd.date_range(start=f"{dte.year}-{dte.month}-01", periods=1, freq='ME')[0].date()

    # print(covid_dataset)
    # print(dte)

    try:
        return int(covid_dataset.loc[np.datetime64(cur_dte), 'New_cases'])
    except KeyError:
        return None


# сбор данных о температуре
def parse_temperature_data(response, dte):
    end = date(dte.year, dte.month, 1)
    d_year = date.today().year - end.year

    # извлечение данных из кода
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('div', class_='chronicle-table')

    # удаляем из полученного списка пустоты, а также берем срез (данные года, соответствующее дате)
    data = list(filter(None, quotes[0].text.split('\n')))[-13 * (d_year + 1): -13 * d_year - 1]

    # проверяем значение при заданном месяце: 999.9 - пустота, температура - иначе
    if data[dte.month - 1] != '999.9':
        return float(data[dte.month - 1])
    else:
        return None


# сбор данных с сайтов
def parse_data(country):
    covid_url = "https://data.who.int/dashboards/covid19/data"
    temp_url = "http://www.pogodaiklimat.ru/history/27612.htm"

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    query = """SELECT id_cntry FROM country WHERE cntry_name = %s;"""
    cursor.execute(query, (country,))
    result = cursor.fetchone()
    if not result:
        query = """
                    INSERT INTO country (id_cntry, cntry_name)
                    VALUES ((SELECT COALESCE(MAX(id_cntry), 0) + 1 FROM country), %s)
                    RETURNING id_cntry;
                    """
        cursor.execute(query, (country,))
        id_cntry = cursor.fetchone()[0]
        conn.commit()
    else:
        id_cntry = result[0]

    query = """SELECT dte 
    FROM information 
    WHERE id_cntry = %s
    ORDER BY dte DESC
    LIMIT 1; 
    """
    cursor.execute(query, (id_cntry,))
    result = cursor.fetchone()
    if not result:
        dte = date(2020, 1, 31)
    else:
        dte = result[0] + relativedelta(months=1)

    cursor.close()
    conn.close()

    # logging.info(f": {type(dte)}, {type(country)}")

    if country == 'Россия':
        country = 'Russian Federation'

    covid_data = parse_covid_data(requests.get(covid_url), dte, country)
    temp_data = parse_temperature_data(requests.get(temp_url), dte)

    # logging.info(f": {covid_data}, {temp_data}")

    if not (temp_data is None) and not (covid_data is None):
        return insert_info(dte, id_cntry, temp_data, covid_data)
    return None


if __name__ == '__main__':
    # print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # parse_temperature_data(requests.get("http://www.pogodaiklimat.ru/history/27612.htm"), date(2021, 5, 1))
    # print(date(2020, 12, 1))
    # parse_data("Russian Federation", date(2020, 12, 1))
    # print(parse_covid_data(requests.get("https://data.who.int/dashboards/covid19/data"),
    #                        date(2020, 1, 31),
    #                        "Russian Federation")
    #       )

    ...
