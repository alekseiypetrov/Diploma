import datetime
import numpy as np
import pandas as pd
from sktime.forecasting.arima import AutoARIMA
from sktime.forecasting.base import ForecastingHorizon
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
import io
import joblib
import psycopg2
import logging

from app.db_pool import DatabasePool


def learning(id_countries):
    # сбор данных из БД
    datasets = get_samples()
    if not datasets:
        return "Возникла ошибка при сборе данных из БД"
    # обучение моделей
    models = fit(datasets)
    del datasets
    # сохранение моделей
    status = save(models, id_countries, datetime.date.today())
    del models
    return status


def get_samples():
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT * FROM information
        ORDER BY (id_cntry, dte);
        """
        cursor.execute(query, )
        dataset = (pd.DataFrame(cursor.fetchall(), columns=["Date", "Id", "Temperature", "Cases"]).
                   astype({"Date": np.datetime64, "Id": int, "Temperature": float, "Cases": int}))
        dataset["Date"] = dataset["Date"] + pd.offsets.MonthEnd(0)
    except Exception as e:
        logging.exception(e)
        return []
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return dataset


# СХЕМА ВОЗВРАЩАЕМОГО ЗНАЧЕНИЯ ФУНКЦИИ fit()
# {
#     <key = id_cntry>:
#         {
#             "SARIMA": <bytes>,
#             "SARIMAX": <bytes>,
#             "LinRegr": <bytes>,
#             "GBR": <bytes>
#         }
# }
def fit(datasets):
    id_countries = np.unique(datasets["Id"].values)
    learned_models = dict(
        zip(id_countries, [{} for _ in range(id_countries.shape[0])])
    )
    for id_country in id_countries:
        temp_train = datasets[datasets["Id"] == id_country]["Temperature"]
        covid_train = datasets[datasets["Id"] == id_country]["New cases"]
        learned_models[id_country]["SARIMA"], _ = fit_sarima(y=temp_train)
        learned_models[id_country]["LinRegr"], y1 = fit_lin_regr(x=temp_train,
                                                                 y=covid_train)
        learned_models[id_country]["SARIMAX"], y2 = fit_sarima(y=temp_train,
                                                               x=covid_train)

        learned_models[id_country]["GBR"] = fit_gbr(meta_x=[y1, y2],
                                                    y=covid_train)
    return learned_models


def fit_sarima(y, x=None):
    if x is not None:
        x["New cases"] = np.log1p(x["New cases"].values)
    model = AutoARIMA(
        error_action='ignore',
        suppress_warnings=True
    ).fit(y=y, X=x)
    model_bytes = io.BytesIO()
    joblib.dump(model, model_bytes)
    model_bytes.seek(0)
    model_bytes = model_bytes.read()
    y_pred = None
    if x is not None:
        fh_dates = pd.date_range(start=y.index[0] + pd.offsets.MonthEnd(0), periods=x.shape[0], freq="ME")
        fh = ForecastingHorizon(fh_dates, is_relative=False)
        y_pred = model.predict(fh=fh, X=x)
    return model_bytes, y_pred


def fit_lin_regr(x, y):
    if isinstance(x, pd.Series):
        x = x.values.reshape(-1, 1)
    y = np.log1p(y)
    model = LinearRegression().fit(X=x, y=y)
    y_pred = model.predict(x)
    model_bytes = io.BytesIO()
    joblib.dump(model, model_bytes)
    model_bytes.seek(0)
    model_bytes = model_bytes.read()
    return model_bytes, y_pred


def fit_gbr(meta_x, y):
    x1, x2 = meta_x[0].values, meta_x[1].values
    if x1.ndim != 2:
        x1 = x1.reshape(-1, 1)
    if x2.ndim != 2:
        x2 = x2.reshape(-1, 1)
    meta_x = np.concatenate([x1, x2], axis=1)
    model = GradientBoostingRegressor(n_estimators=250, learning_rate=0.2)
    model.fit(meta_x, y)
    model_bytes = io.BytesIO()
    joblib.dump(model, model_bytes)
    model_bytes.seek(0)
    model_bytes = model_bytes.read()
    return model_bytes


def save(models, id_countries, dte):
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """INSERT INTO ai_models (id_cntry, model_name, model_file, dte)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id_cntry, model_name) DO 
                    UPDATE SET model_file = EXCLUDED.model_file, dte = EXCLUDED.dte;
                    """
        for id_country in sorted(id_countries):
            cursor.execute(query, (id_country, "SARIMA", psycopg2.Binary(models[id_country]["SARIMA"]), dte))
            cursor.execute(query, (id_country, "LinRegr", psycopg2.Binary(models[id_country]["LinRegr"]), dte))
            cursor.execute(query, (id_country, "SARIMAX", psycopg2.Binary(models[id_country]["SARIMAX"]), dte))
            cursor.execute(query, (id_country, "GBR", psycopg2.Binary(models[id_country]["GBR"]), dte))
    except Exception as e:
        logging.exception(e)
        return "Не все модели были обучены и сохранены"
    finally:
        database.commit()
        cursor.close()
        DatabasePool.release_connection(database)
    return "Все модели обучены и сохранены"
