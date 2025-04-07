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


def learning():  # id_countries):  # -> Str
    # сбор данных из БД
    datasets = get_samples()
    if datasets.empty:
        return "Возникла ошибка при сборе данных из БД"
    # обучение моделей
    models = fit(datasets)
    # сохранение моделей
    status = save(models, np.unique(datasets["Id"].values), datetime.date.today())
    del datasets
    del models
    return status


def get_samples():  # -> Pandas.DataFrame()
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
        logging.exception(e)
        return pd.DataFrame()
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
def fit(datasets):  # -> Dict( <Int>: Dict(<Str>: <io.Bytes()>) )
    id_countries = np.unique(datasets["Id"].values)
    learned_models = dict(
        zip(id_countries, [{} for _ in range(id_countries.shape[0])])
    )
    for id_country in id_countries:
        temp_train = datasets[datasets["Id"] == id_country][["Date", "Temperature"]].set_index("Date")
        covid_train = datasets[datasets["Id"] == id_country][["Date", "Cases"]].set_index("Date")
        learned_models[id_country]["SARIMA"], _ = fit_sarima(y=temp_train)
        learned_models[id_country]["LinRegr"], y1 = fit_lin_regr(x=temp_train["Temperature"].values,
                                                                 y=covid_train["Cases"].values)
        learned_models[id_country]["SARIMAX"], y2 = fit_sarima(y=covid_train,
                                                               x=temp_train)

        learned_models[id_country]["GBR"] = fit_gbr(meta_x=[y1, y2],
                                                    y=covid_train["Cases"].values)
    return learned_models


def fit_sarima(y, x=None):  # -> ( io.Bytes(), NumPy.ndarray )
    seasonal = True
    if x is not None:
        seasonal = False
        y["Cases"] = np.log1p(y["Cases"].values)
    model = AutoARIMA(
        seasonal=seasonal,
        error_action='ignore',
        suppress_warnings=True
    ).fit(y=y, X=x)
    model_bytes = io.BytesIO()
    joblib.dump(model, model_bytes)
    model_bytes.seek(0)
    model_bytes = model_bytes.read()
    y_pred = np.array([])
    if x is not None:
        fh_dates = pd.date_range(start=y.index[0] + pd.offsets.MonthEnd(0), periods=x.shape[0], freq="ME")
        fh = ForecastingHorizon(fh_dates, is_relative=False)
        y_pred = model.predict(fh=fh, X=x).values
        # если есть NaN в прогнозах, заменить на среднее значение всех не NaN элементов
        mask = np.isnan(y_pred)
        y_pred[mask] = 0 if y_pred[~mask].size == 0 else y_pred[~mask].mean()
        # if y_pred[~np.isnan(y_pred)].size == 0:
        #     y_pred[np.isnan(y_pred)] = 0
        # else:
        #     y_pred[np.isnan(y_pred)] = y_pred[~np.isnan(y_pred)].mean()
    return model_bytes, y_pred


def fit_lin_regr(x, y):  # -> ( io.Bytes(), NumPy.ndarray )
    x = x.reshape(-1, 1)
    y = np.log1p(y)
    model = LinearRegression().fit(X=x, y=y)
    y_pred = model.predict(x)
    # в случае возникновения NaN в прогнозах, заменить на среднее значение всех не NaN элементов
    mask = np.isnan(y_pred)
    y_pred[mask] = 0 if y_pred[~mask].size == 0 else y_pred[~mask].mean()
    # if y_pred[~np.isnan(y_pred)].size == 0:
    #     y_pred[np.isnan(y_pred)] = 0
    # else:
    #     y_pred[np.isnan(y_pred)] = y_pred[~np.isnan(y_pred)].mean()
    model_bytes = io.BytesIO()
    joblib.dump(model, model_bytes)
    model_bytes.seek(0)
    model_bytes = model_bytes.read()
    return model_bytes, y_pred


def fit_gbr(meta_x, y):  # -> io.Bytes()
    x1, x2 = meta_x[0], meta_x[1]
    x1 = x1.reshape(-1, 1)
    x2 = x2.reshape(-1, 1)
    meta_x = np.concatenate([x1, x2], axis=1)
    y = np.log1p(y)
    model = GradientBoostingRegressor(n_estimators=250, learning_rate=0.2)
    model.fit(meta_x, y)
    model_bytes = io.BytesIO()
    joblib.dump(model, model_bytes)
    model_bytes.seek(0)
    model_bytes = model_bytes.read()
    return model_bytes


def save(models, id_countries, dte):  # -> Str
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """INSERT INTO ai_models (id_cntry, model_name, model_file, dte)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id_cntry, model_name) DO 
                    UPDATE SET model_file = EXCLUDED.model_file, dte = EXCLUDED.dte;
                    """
        for id_country in id_countries:  # sorted(id_countries):
            cursor.execute(query, (int(id_country), "SARIMA", psycopg2.Binary(models[id_country]["SARIMA"]), dte))
            cursor.execute(query, (int(id_country), "LinRegr", psycopg2.Binary(models[id_country]["LinRegr"]), dte))
            cursor.execute(query, (int(id_country), "SARIMAX", psycopg2.Binary(models[id_country]["SARIMAX"]), dte))
            cursor.execute(query, (int(id_country), "GBR", psycopg2.Binary(models[id_country]["GBR"]), dte))
    except Exception as e:
        logging.exception(e)
        return "Не все модели были обучены и сохранены"
    finally:
        database.commit()
        cursor.close()
        DatabasePool.release_connection(database)
    return "Все модели обучены и сохранены"
