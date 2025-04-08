import datetime
import numpy as np
import pandas as pd
from sktime.forecasting.base import ForecastingHorizon
from PIL import Image
import matplotlib.pyplot as plt
import io
import joblib

from db_pool import DatabasePool


def get_prediction(country):
    models, date = get_models_and_date(country)
    fh_date = pd.date_range(start=date + pd.offsets.MonthEnd(1), periods=12, freq="ME")
    fh = ForecastingHorizon(fh_date, is_relative=False)
    date = [f"{fh_date[0].year}-{fh_date[0].month}", f"{fh_date[-1].year}-{fh_date[-1].month}"]

    predicted_temp, predicted_covid = forecast(fh, models)

    fig, axes = plt.subplots(1, 2, figsize=(15, 10))
    fig.suptitle(f"Прогноз температуры и заболеваемости с {date[0]} по {date[-1]} ({country})")

    axes[0].plot(fh_date, predicted_temp)
    axes[0].grid(linestyle='--')
    axes[0].set_ylabel("Температура")
    for label in axes[0].get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
    axes[1].plot(fh_date, predicted_covid)
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


def get_models_and_date(country):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        # получаем id страны
        query = """SELECT id_cntry FROM country
        WHERE cntry_name = %s;
        """
        cursor.execute(query, (country,))
        result = cursor.fetchone()
        if not result:
            raise Exception
        id_cntry = result[0]

        # получаем все модели
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

        # получаем последнюю дату сбора
        query = """SELECT dte FROM information
        WHERE id_cntry = %s
        ORDER BY dte DESC LIMIT 1;
        """
        cursor.execute(query, (id_cntry,))
        result = cursor.fetchone()
        if not result:
            raise Exception
        dte = result[0]
    except Exception as e:
        return {}, datetime.date(2020, 1, 1)
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return models, dte


def forecast(fh, models):
    # в случае возникновения NaN в прогнозах, заменить на среднее значение всех не NaN элементов
    # def nan_correction(x):
    #     mask = np.isnan(x)
    #     x[mask] = 0 if x[~mask].size == 0 else x[~mask].mean()
    #     return x

    predicted_temp = models["SARIMA"].predict(fh=fh)
    x_pred = predicted_temp.values.reshape(-1, 1)
    y1 = models["LinRegr"].predict(x_pred)
    y2 = models["SARIMAX"].predict(fh=fh, X=predicted_temp).values
    y1 = y1.reshape(-1, 1)
    y2 = y2.reshape(-1, 1)
    meta_y = np.concatenate((y1, y2), axis=1)
    predicted_covid = np.expm1(models["GBR"].predict(meta_y)).astype(int)
    return predicted_temp, predicted_covid
