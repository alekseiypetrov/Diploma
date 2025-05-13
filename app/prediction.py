import datetime
import pandas as pd
from sktime.forecasting.base import ForecastingHorizon

from tools.tools.db_queries import get_one_id, get_date
from tools.tools.model_manager import get_models, forecast, paint_results


def get_prediction(country):
    models, date = get_models_and_date(country)
    fh_date = pd.date_range(start=date + pd.offsets.MonthEnd(1), periods=12, freq="ME")
    fh = ForecastingHorizon(fh_date, is_relative=False)
    date = [f"{fh_date[0].year}-{fh_date[0].month}", f"{fh_date[-1].year}-{fh_date[-1].month}"]

    predicted_temp, predicted_covid = forecast(fh, models)

    return paint_results(f"Прогноз температуры и заболеваемости с {date[0]} по {date[-1]} ({country})",
                         fh_date,
                         predicted_temp,
                         predicted_covid)


def get_models_and_date(country):
    id_cntry = get_one_id(country)
    if not id_cntry:
        return {}, datetime.date(2020, 1, 1)
    models = get_models(id_cntry)
    dte = get_date(from_table="information", is_end=True)
    if not models or not dte:
        return {}, datetime.date(2020, 1, 1)
    return models, dte
