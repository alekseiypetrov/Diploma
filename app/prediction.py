import datetime
import numpy as np
import pandas as pd
from sktime.forecasting.arima import AutoARIMA
from sktime.forecasting.base import ForecastingHorizon
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
import io
import joblib

from app.db_pool import DatabasePool


def predict():
    pass


def get_models():
    pass


def temp_pred():
    pass


if __name__ == '__main__':
    a = 5
    # df = (pd.read_csv("D:\\Университет\\4 курс\\Диплом\\Программная реализация\\Датасеты (объединенные)\\Россия.csv").
    #       astype({"Date": 'datetime64[ns]', "Temperature": float, "New cases": int}))
    # df["Date"] = df["Date"] + pd.offsets.MonthEnd(0)
    # y = df[["Date", "Temperature"]].set_index("Date")
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
    # ).fit(y=y, X=X)
    # fh_dates = pd.date_range(start=y.index[0] + pd.offsets.MonthEnd(0), periods=14, freq="ME")
    # fh = ForecastingHorizon(fh_dates, is_relative=False)
    # X_pred = None
    # X_pred = pd.DataFrame({"Date": fh_dates,
    #                        "New cases": [0, 0, 0]}).set_index("Date")
    # y_pred = model.predict(fh=fh, X=X_pred)
    # print(y_pred)

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
