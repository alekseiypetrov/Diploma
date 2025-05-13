from tools.tools.db_pool import DatabasePool
import io
import joblib
import pandas as pd
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
from PIL import Image


# метрика WAPE для оценки качества модели SARIMA для прогноза температуры
def weighted_average_percentage_error(y_true, y_pred):
    return np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))


# получение моделей из БД
def get_models(id_cntry):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        models = {}
        query = """SELECT model_name, model_file FROM ai_models
                WHERE id_cntry = %s;
                """
        cursor.execute(query, (id_cntry,))
        result = cursor.fetchall()
        if not result:
            raise Exception
        for (model_name, model_bytes) in result:
            models[model_name] = joblib.load(io.BytesIO(model_bytes))
    except Exception as e:
        models = {}
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return models


# сохранение обученных моделей
def save_fit_models(models, id_countries, dte):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """INSERT INTO ai_models (id_cntry, model_name, model_file, dte)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id_cntry, model_name) DO 
                        UPDATE SET model_file = EXCLUDED.model_file, dte = EXCLUDED.dte;
                        """
        for id_country in id_countries:
            cursor.execute(query, (int(id_country), "SARIMA", psycopg2.Binary(models[id_country]["SARIMA"]), dte))
            cursor.execute(query, (int(id_country), "LinRegr", psycopg2.Binary(models[id_country]["LinRegr"]), dte))
            cursor.execute(query, (int(id_country), "SARIMAX", psycopg2.Binary(models[id_country]["SARIMAX"]), dte))
            cursor.execute(query, (int(id_country), "GBR", psycopg2.Binary(models[id_country]["GBR"]), dte))
    except Exception as e:
        return "Не все модели были обучены и сохранены"
    finally:
        database.commit()
        cursor.close()
        DatabasePool.release_connection(database)
    return "Все модели обучены и сохранены"


# получение истинных данных по стране
def get_true_values(id_cntry):  # -> Pandas.DataFrame()
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT dte, temperature, new_cases FROM information
        WHERE id_cntry = %s
        ORDER BY dte;
        """
        cursor.execute(query, (id_cntry,))
        dataset = (pd.DataFrame(cursor.fetchall(), columns=["Date", "Temperature", "Cases"]).
                   astype({"Date": 'datetime64[ns]', "Temperature": float, "Cases": int}))
        dataset["Date"] = dataset["Date"] + pd.offsets.MonthEnd(0)
    except Exception as e:
        return pd.DataFrame()
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return dataset


# получение исходных данных для обучения
def get_samples():
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT * FROM information
        ORDER BY (id_cntry, dte);
        """
        cursor.execute(query, )
        dataset = (pd.DataFrame(cursor.fetchall(), columns=["Date", "Id", "Temperature", "Cases"]).
                   astype({"Date": 'datetime64[ns]', "Id": int, "Temperature": float, "Cases": int}))
        dataset["Date"] = dataset["Date"] + pd.offsets.MonthEnd(0)
    except Exception as e:
        return pd.DataFrame()
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return dataset


# предсказание значений
def forecast(fh, models):
    # в случае возникновения NaN в прогнозах, заменить на среднее значение всех не NaN элементов
    def nan_correction(x):
        mask = np.isnan(x)
        x[mask] = 0 if x[~mask].size == 0 else x[~mask].mean()
        return x

    predicted_temp = models["SARIMA"].predict(fh=fh)
    x_pred = predicted_temp.values.reshape(-1, 1)
    y1 = nan_correction(models["LinRegr"].predict(x_pred))
    y2 = nan_correction(models["SARIMAX"].predict(fh=fh, X=predicted_temp).values)
    y1 = y1.reshape(-1, 1)
    y2 = y2.reshape(-1, 1)
    meta_y = np.concatenate((y1, y2), axis=1)
    predicted_covid = np.expm1(models["GBR"].predict(meta_y)).astype(int)
    return predicted_temp, predicted_covid


def paint_results(title, date, temp, covid, true_values=None):
    fig, axes = plt.subplots(1, 2, figsize=(15, 10))
    fig.suptitle(title)

    if true_values is None:
        axes[0].plot(date, temp)
    else:
        axes[0].plot(date, temp, label="Данные модели")
        axes[0].plot(date, true_values["Temperature"].values, label="Исходные данные")
        axes[0].legend()
    axes[0].grid(linestyle='--')
    axes[0].set_ylabel("Температура")
    for label in axes[0].get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
    if true_values is None:
        axes[1].plot(date, covid)
    else:
        axes[1].plot(date, covid, label="Данные модели")
        axes[1].plot(date, true_values["Cases"].values, label="Исходные данные")
        axes[1].legend()
    axes[1].grid(linestyle='--')
    axes[1].set_ylabel("Новые случаи заболеваемости")
    for label in axes[1].get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    plt.close()
    img = Image.open(img_bytes)
    output_img = Image.new('RGB', img.size)
    output_img.paste(img, (0, 0))
    return output_img
