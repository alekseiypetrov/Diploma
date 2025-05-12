import numpy as np
import pandas as pd
from sktime.forecasting.base import ForecastingHorizon
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from PIL import Image
import matplotlib.pyplot as plt
import io
import joblib

from app.db_pool import DatabasePool


def get_error(country):
    date = get_date()
    periods = 24 + date[-1].month
    fh_date = pd.date_range(start=date[0] + pd.offsets.MonthEnd(0), periods=periods, freq="ME")
    fh = ForecastingHorizon(fh_date, is_relative=False)
    date = [f"{fh_date[0].year}-{fh_date[0].month}", f"{fh_date[-1].year}-{fh_date[-1].month}"]

    id_cntry = get_id(country)
    if id_cntry is None:
        return f"Нет страны {country} в БД", 400
    models = get_models(id_cntry)
    if not models:
        return f"Нет моделей страны {country}", 400
    true_values = get_true_values(id_cntry)
    if true_values.empty:
        return f"В БД нет данных по стране {country}", 400
    predicted_temp, predicted_covid = forecast(fh, models)
    wape, rmse, mae = (
        weighted_average_percentage_error(true_values["Temperature"].values, predicted_temp.values),
        root_mean_squared_error(true_values["Cases"].values, predicted_covid),
        mean_absolute_error(true_values["Cases"].values, predicted_covid),
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 10))
    fig.suptitle(f"Ошибки прогнозирования: температура и заболеваемость ({country})")
    axes[0].plot(fh_date, predicted_temp, label="Данные модели")
    axes[0].plot(fh_date, true_values["Temperature"].values, label="Исходные данные")
    axes[0].grid(linestyle='--')
    axes[0].set_ylabel("Температура")
    axes[0].set_ylabel("Температура")
    for label in axes[0].get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
    axes[0].legend()
    axes[1].plot(fh_date, predicted_covid, label="Данные модели")
    axes[1].plot(fh_date, true_values["Cases"].values, label="Исходные данные")
    axes[1].grid(linestyle='--')
    axes[1].set_ylabel("Новые случаи заболеваемости")
    for label in axes[1].get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
    axes[1].legend()

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    plt.close()
    img = Image.open(img_bytes)
    output_img = Image.new('RGB', img.size)
    output_img.paste(img, (0, 0))
    return output_img, [round(wape, 2), round(rmse, 2), round(mae, 2)]


def weighted_average_percentage_error(y_true, y_pred):
    return np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))


def get_date():  # -> List()
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        date = []
        # получаем первую дату сбора
        query = """SELECT dte FROM information
                ORDER BY dte LIMIT 1;
                """
        cursor.execute(query, )
        result = cursor.fetchone()
        if not result:
            raise Exception
        date.append(result[0])
        # получаем последнюю дату сбора
        query = """SELECT dte FROM information
                ORDER BY dte DESC LIMIT 1;
                """
        cursor.execute(query, )
        result = cursor.fetchone()
        if not result:
            raise Exception
        date.append(result[0])
    except Exception as e:
        return []
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return date


def get_id(country):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT id_cntry FROM country
                WHERE cntry_name = %s;
                """
        cursor.execute(query, (country,))
        result = cursor.fetchone()
        if not result:
            raise Exception
        id_cntry = result[0]
    except Exception as e:
        return None
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return id_cntry


def get_models(id_cntry):  # -> Dict()
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        models = {}
        query = """SELECT model_name, model_file FROM ai_models WHERE id_cntry = %s;"""
        cursor.execute(query, (id_cntry,))
        for (model_name, model_bytes) in cursor.fetchall():
            models[model_name] = joblib.load(io.BytesIO(model_bytes))
    except Exception as e:
        return {}
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return models


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
