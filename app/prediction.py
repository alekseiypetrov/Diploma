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
    axes[0].set_title(f"Прогноз температуры и заболеваемости с {date[0]} по {date[-1]} ({country})")
    # axes[1].set_title(f"Прогноз заболеваемости с {dates[0]} по {dates[1]} ({country})")

    axes[0].plot(fh_date, predicted_temp)
    axes[0].grid(linestyle='--')
    axes[1].plot(fh_date, predicted_covid)
    axes[1].grid(linestyle='--')

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

    # predicted_temp = nan_correction(models["SARIMA"].predict(fh=fh).values)
    # x_pred = predicted_temp.reshape(-1, 1)
    # y1 = nan_correction(models["LinRegr"].predict(x_pred))
    # y2 = nan_correction(models["SARIMAX"].predict(fh=fh, X=x_pred).values)
    # y1 = y1.reshape(-1, 1)
    # y2 = y2.reshape(-1, 1)
    # meta_y = np.concatenate((y1, y2), axis=1)
    # predicted_covid = nan_correction(np.expm1(models["GBR"].predict(meta_y))).astype(int)
    return predicted_temp, predicted_covid

# if __name__ == '__main__':
# a = np.array([np.nan, np.nan, 1, 2, 3])
# a = np.array([5, 5, 1, 2, 3])
# a = np.array([np.nan, np.nan, np.nan, np.nan, np.nan])
# print(np.array([[]]).size)
# print(a[~np.isnan(a)], a[~np.isnan(a)].mean())
# a[np.isnan(a)] = a[~np.isnan(a)].mean()
# a = np.nan_to_num(a, other.mean())
# print(a)
# print(type(pd.DataFrame().values))
# a = {1: 1, 2: 2, 3: 3}
# keys = {3, 1}
# print(type(keys), type(set(a.keys())))
# a = {}
# print(set(a.keys()) == keys)
# print(1 in a.keys())
# print(a[4])

# fh_dates = pd.date_range(start=datetime.date.today() + pd.offsets.MonthEnd(0), periods=12, freq="ME")
# dates = [f"{fh_dates[0].year}-{fh_dates[0].month}", f"{fh_dates[-1].year}-{fh_dates[-1].month}"]
# print(dates)
# print(fh_dates[0].year)
# df = (pd.read_csv("D:\\Университет\\4 курс\\Диплом\\Программная реализация\\Датасеты (объединенные)\\Россия.csv").
#       astype({"Date": 'datetime64[ns]', "Temperature": float, "New cases": int}))
# df["Date"] = df["Date"] + pd.offsets.MonthEnd(0)
# y = df[["Date", "Temperature"]].set_index("Date")
# print(type(y))
# X = None
# X = df[["Date", "New cases"]].set_index("Date")
# X["New cases"] = np.log1p(X["New cases"].values)
# print(X)
# print(pd.date_range(start=datetime.date.today(), periods=3, freq="ME"))
#
# print(pd.DataFrame({"Date": pd.date_range(start=datetime.date.today(), periods=3, freq="ME"),
#                     "New cases": [0, 0, 0]}).set_index("Date"))
#
# model = AutoARIMA(
#     error_action='ignore',
#     suppress_warnings=True
# ).fit(y=y)  # , X=X)
# fh_dates = pd.date_range(start=y.index[0] + pd.offsets.MonthEnd(0), periods=14, freq="ME")
# fh = ForecastingHorizon(fh_dates, is_relative=False)
# X_pred = None
# X_pred = pd.DataFrame({"Date": fh_dates,
#                        "New cases": [0, 0, 0]}).set_index("Date")
# y_pred = (model.predict(fh=fh).  # , X=X_pred).
#           fillna(0))
# print(type(y_pred))
# print(type(y_pred) == type(y))
# print(y_pred)
# print(y_pred.values)
# print(df.iloc[:, 0])

# a = [(1, 2, 3, 4), (2, 1, 4, 3), (1, 2, 4, 5), (1, 2, 5, 6), (2, 4, 6, 8)]
# dfd = pd.DataFrame(a, columns=["id", "dte", 't', 'c'])
# print(dfd[dfd["id"] == 2])
# print(type(dfd["id"].values))
# arr = np.unique(dfd["id"].values)
# print(arr)
#
# d = dict(
#     zip(arr, [{} for _ in range(arr.shape[0])])
# )
# d[2]["SARIMA"] = "Hello"
# print(d[2])
