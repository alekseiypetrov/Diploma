import datetime
import numpy as np
import pandas as pd
from sktime.forecasting.arima import AutoARIMA
from sktime.forecasting.base import ForecastingHorizon
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
import io
import joblib

from db_pool import DatabasePool


def predict():
    pass


def get_models():
    pass


def temp_pred():
    pass


if __name__ == '__main__':
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
    a = 5
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

    # print(pd.DataFrame({"Date": pd.date_range(start=datetime.date.today(), periods=3, freq="ME"),
    #                     "New cases": [0, 0, 0]}).set_index("Date"))

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
    # d = dict(
    #     zip(arr, [{} for _ in range(arr.shape[0])])
    # )
    # d[2]["SARIMA"] = "Hello"
    # print(d[2])
