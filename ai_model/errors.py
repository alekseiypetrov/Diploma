import pandas as pd
from sktime.forecasting.base import ForecastingHorizon
from sklearn.metrics import root_mean_squared_error, mean_absolute_error

from tools.tools.db_queries import get_one_id, get_date
from tools.tools.model_manager import (get_models, get_true_values,
                                       weighted_average_percentage_error, forecast, paint_results)


def get_error(country):
    date = [
        get_date(from_table="information", is_end=False),
        get_date(from_table="information", is_end=True)
    ]
    periods = 24 + date[-1].month
    fh_date = pd.date_range(start=date[0] + pd.offsets.MonthEnd(0), periods=periods, freq="ME")
    fh = ForecastingHorizon(fh_date, is_relative=False)

    id_cntry = get_one_id(country)
    if not id_cntry:
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

    return (paint_results(
        f"Ошибки прогнозирования: температура и заболеваемость ({country})",
        fh_date,
        predicted_temp,
        predicted_covid,
        true_values=true_values
    ),
            [round(wape, 2), round(rmse, 2), round(mae, 2)])
