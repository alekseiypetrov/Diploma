import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import date
from insert_data import extract_info

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# импорт стран из json-файла
def import_countries():
    file_path = os.path.join(BASE_DIR, "links", "temperature sources.json")
    return pd.read_json(file_path)


# сбор данных о заболеваемости
def parse_covid_data(dte, countries):
    # импорт ковидной ссылки
    file_path = os.path.join(BASE_DIR, "links", "covid link.bin")
    with open(file_path, mode='rb') as f:
        covid_url = f.readline().decode()

    response = requests.get(covid_url)
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('a', class_='btn btn-primary btn-sm')
    file_url = quotes[0]['href']

    covid_dataset = (pd.read_csv(file_url).
                     drop(['Country_code', 'WHO_region', 'Cumulative_cases', 'New_deaths', 'Cumulative_deaths'],
                          axis=1).
                     set_index("Date_reported"))

    covid_dataset = covid_dataset[covid_dataset['Country'].isin(countries)]
    covid_dataset.index = pd.to_datetime(covid_dataset.index)
    covid_dataset['New_cases'] = covid_dataset['New_cases'].fillna(0)

    cur_dte = pd.date_range(start=f"{dte.year}-{dte.month}-01", periods=1, freq='ME')[0].date()
    covid_data = []
    try:
        for country in countries:
            covid_data.append((country,
                               int((covid_dataset[covid_dataset['Country'] == country].resample('ME').sum()).loc[
                                       np.datetime64(cur_dte), 'New_cases'])
                               )
                              )
        return pd.DataFrame(covid_data, columns=["en_country", "new_cases"]).set_index("en_country")
    except KeyError:
        return None


# сбор данных о температуре
def parse_temperature_data(url, dte):
    response = requests.get(url)

    end = date(dte.year, dte.month, 1)
    d_year = date.today().year - end.year

    # извлечение данных из кода
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('div', class_='chronicle-table')

    # удаляем из полученного списка пустоты, а также берем срез (данные года, соответствующее дате)
    data = list(filter(None, quotes[0].text.split('\n')))[-13 * (d_year + 1): -13 * d_year - 1]

    # проверяем значение при заданном месяце: 999.9 - пустота, температура - иначе
    if data[dte.month - 1] == '999.9':
        return None
    return float(data[dte.month - 1])


# сбор данных с сайтов
def parse_data():
    # импорт стран, получение главной таблицы
    table_of_countries = import_countries()

    # получение таблицы с id стран и даты, объединение с главной таблицей
    id_countries, dte = extract_info(tuple(sorted(table_of_countries.country.values)))
    table_of_countries = table_of_countries.join(id_countries, on="country", how="left").astype({"id": int})
    table_of_countries.insert(3, "dte",
                              pd.Series(np.full(shape=table_of_countries.shape[0], fill_value=dte))
                              )

    # сбор температуры и объединение с главной таблицей
    temp_data = []
    for element in table_of_countries.values:
        temperature = parse_temperature_data(element[2], dte)
        if temperature is None:
            return f"Возникла ошибка при сборе данных температуры для даты {dte}"
        temp_data.append((element[0], temperature))
    temperature_data = pd.DataFrame(temp_data, columns=["country", "temperature"]).set_index("country")
    table_of_countries = (table_of_countries.join(temperature_data, on="country", how="left").
                          astype({"temperature": float}))

    # сбор ковида и объединение с главной таблицей
    covid_data = parse_covid_data(dte, tuple(sorted(table_of_countries.en_country.values)))
    if covid_data is None:
        return f"Возникла ошибка при сборе данных заболеваемости для даты {dte}"
    table_of_countries = table_of_countries.join(covid_data, on="en_country", how="left").astype({"new_cases": int})
    return table_of_countries
