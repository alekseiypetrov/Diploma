import datetime
from app.db_pool import DatabasePool
import numpy as np
import pandas as pd
from sktime.forecasting.arima import AutoARIMA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
import io
import joblib


def learning(id_countries):
    result = {
        "status": "Обучение моделей",
        "temp": "",
        "covid": ""
    }
    # сбор данных из БД
    datasets = get_samples(id_countries)
    # обучение моделей
    models = fit(datasets)
    del datasets
    # сохранение моделей
    save(models)
    return result


def get_samples(id_countries):
    return pd.DataFrame()

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
    return True


def save(models):
    pass


# обучение ансамбля по ковиду
def fit_covid_models(countries):
    def fit(X, y, id_cntry):
        y = np.log1p(y)
        # Обучение регрессии
        reg_model = LinearRegression().fit(X=X, y=y)
        # Обучение SARIMAX
        sarimax_model = AutoARIMA(
            error_action='ignore',
            suppress_warnings=True
        ).fit(y=y, X=X)
        # Формирование обучающей выборки для стэкера
        x1 = reg_model.predict(X)
        x2 = sarimax_model.predict(n_periods=X.shape[0], X=X)
        if x1.ndim != 2:
            x1 = x1.reshape(-1, 1)
        if x2.ndim != 2:
            x2 = x2.reshape(-1, 1)
        meta_x_train = np.concatenate((x1, x2), axis=1)
        # Обучение стэкера
        stacker = GradientBoostingRegressor(n_estimators=500, learning_rate=0.2)
        stacker.fit(meta_x_train, y)
        # Сохранение моделей
        models_bytes = {
            "LinearRegression": io.BytesIO(),
            "SARIMAX": io.BytesIO(),
            "GBR": io.BytesIO()
        }
        joblib.dump(reg_model, models_bytes["LinearRegression"])
        joblib.dump(sarimax_model, models_bytes["SARIMAX"])
        joblib.dump(stacker, models_bytes["GBR"])

        database = DatabasePool.get_connection()
        try:
            cursor = database.cursor()
            query = """INSERT INTO ai_models (id_cntry, model_name, model_file, dte)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id_cntry, model_name) DO UPDATE SET model_file = EXCLUDED.model_file, dte = EXCLUDED.dte;
            """
            for model_name in models_bytes:
                models_bytes[model_name].seek(0)
                cursor.execute(query,
                               (id_cntry,
                                model_name,
                                models_bytes[model_name].getvalue(),
                                datetime.datetime.today().date())
                               )
            database.commit()
            cursor.close()
        except Exception as e:
            return False
        finally:
            DatabasePool.release_connection(database)
        return True

    def get_samples(my_dataset):
        samples = {}
        database = DatabasePool.get_connection()
        try:
            cursor = database.cursor()
            query = """SELECT temperature, new_cases FROM information
                    WHERE id_cntry = %s
                    ORDER BY dte;
                    """
            for i in my_dataset.shape[0]:
                samples[my_dataset.iloc[i, 0]] = pd.DataFrame(
                    cursor.execute(query, (my_dataset.iloc[i, 1])).fetchall(),
                    columns=["temp", "new_cases"]
                ).astype({'temp': 'float', 'new_cases': 'int'})
            cursor.close()
        except Exception as e:
            samples = {}
        finally:
            DatabasePool.release_connection(database)
        return samples

    dataset = get_samples(countries)
    bool_logs = []
    crush_countries = []
    for i, country in enumerate(dataset):
        bool_logs.append(fit(X=dataset[country].iloc[:, 0].values.reshape(-1, 1),
                             y=dataset[country].iloc[:, 1].values,
                             id_cntry=countries.iloc[i, 1])
                         )
        if not bool_logs[-1]:
            crush_countries.append(country)
    if not all(bool_logs):
        return f"Не все модели обучены и сохранены ({','.join(crush_countries)})."
    return "Все модели успешно обучены и сохранены в БД."


# обучение по температуре
def fit_temp_models(countries):
    def fit(x, id_cntry):
        model = AutoARIMA(
            error_action='ignore',
            suppress_warnings=True
        ).fit(y=x.iloc[:])
        try:
            model_bytes = io.BytesIO()
            joblib.dump(model, model_bytes)
            model_bytes.seek(0)

            database = DatabasePool.get_connection()
            cursor = database.cursor()
            query = """INSERT INTO ai_models (id_cntry, model_name, model_file, dte)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id_cntry, model_name) DO UPDATE SET model_file = EXCLUDED.model_file, dte = EXCLUDED.dte;
            """
            cursor.execute(query, (id_cntry, "SARIMA", model_bytes.getvalue(), datetime.datetime.today().date()))
            database.commit()
            cursor.close()
        except Exception as e:
            return False
        finally:
            DatabasePool.release_connection(database)
        return True

    def get_samples(my_dataset):
        samples = {}
        database = DatabasePool.get_connection()
        try:
            cursor = database.cursor()
            query = """SELECT temperature FROM information
            WHERE id_cntry = %s
            ORDER BY dte;
            """
            for i in my_dataset.shape[0]:
                samples[my_dataset.iloc[i, 0]] = (np.array(cursor.execute(query, (my_dataset.iloc[i, 1])).fetchall()).
                                                  astype('float'))
            cursor.close()
        except Exception as e:
            samples = {}
        finally:
            DatabasePool.release_connection(database)
        return samples

    dataset = get_samples(countries)
    bool_logs = []
    crush_countries = []
    for i, country in enumerate(dataset):
        bool_logs.append(fit(dataset[country], countries.iloc[i, 1]))
        if not bool_logs[-1]:
            crush_countries.append(country)
    if not all(bool_logs):
        return f"Не все модели обучены и сохранены ({','.join(crush_countries)})."
    return "Все модели успешно обучены и сохранены в БД."
