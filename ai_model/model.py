from flask import Flask, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import signal
import base64
import io

from app.db_pool import DatabasePool
from scheduler import scheduled_learn, log
from errors import get_error

app = Flask(__name__, static_url_path='/static')
scheduler_learn = BackgroundScheduler()
scheduler_learn.add_job(scheduled_learn, 'interval', minutes=10)


@app.route('/')
def interface():
    logging.info("Запрос к странице ИИ-модели")
    database = DatabasePool.get_connection()
    cursor = database.cursor()
    try:
        query = """SELECT cntry_name FROM country
            ORDER BY cntry_name;"""
        cursor.execute(query, )
        countries = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        countries = []
    finally:
        cursor.close()
        DatabasePool.release_connection(database)
    return render_template("ai_page.html", log=log, countries=countries)


@app.route('/quality', methods=['POST'])
def show_quality():
    country = request.form.get('country')
    img, metrics = get_error(country)
    if type(img) is str and type(metrics) is int:
        return img, metrics
    new_img = io.BytesIO()
    img.save(new_img, format='PNG')
    new_img.seek(0)
    img_base64 = base64.b64encode(new_img.read()).decode('utf-8')
    return render_template('show_quality.html', image_data=img_base64, metrics=metrics)


def initialize_services():
    logging.info("Инициализация сервиса...")
    DatabasePool.init_pool()
    scheduler_learn.start()
    logging.info("Сервис инициализирован.")


# Закрытие пула соединений и остановка планировщиков
def shutdown_services(*args):
    logging.info("Завершение работы сервиса...")
    scheduler_learn.shutdown()
    DatabasePool.close_pool()
    logging.info("Сервис завершил работу.")
    exit(0)


if __name__ == '__main__':
    # Инициализация сервисов
    initialize_services()

    # Обработка сигнала завершения (CTRL+C или завершение процесса)
    signal.signal(signal.SIGINT, shutdown_services)
    signal.signal(signal.SIGTERM, shutdown_services)

    try:
        app.run(host='0.0.0.0', port=5002)
    except Exception as e:
        logging.error("Ошибка в работе приложения: %s", e)
    finally:
        shutdown_services()
