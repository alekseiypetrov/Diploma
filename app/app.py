from flask import Flask, render_template, request
import io
import base64
import os
import logging

from tools.tools.db_pool import DatabasePool
from tools.tools.db_queries import get_countries
from tools.tools.file_manager import get_status
from errors import get_error
from rendering import get_image
from prediction import get_prediction

app = Flask(__name__, static_url_path='/static')
BASE_DIR = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]


@app.route('/')
def home():
    countries = get_countries()
    return render_template('index.html', countries=countries)


@app.route('/show_plot')
def show_data():
    mode = request.args.get('mode')
    img = get_image(mode)
    if type(img) is str:
        return img, 400
    new_img = io.BytesIO()
    img.save(new_img, format='PNG')
    new_img.seek(0)
    img_base64 = base64.b64encode(new_img.read()).decode('utf-8')
    return render_template('show_plot.html', image_data=img_base64)


@app.route('/prediction')
def prediction():
    country = request.args.get('country')
    img = get_prediction(country)
    new_img = io.BytesIO()
    img.save(new_img, format='PNG')
    new_img.seek(0)
    img_base64 = base64.b64encode(new_img.read()).decode('utf-8')
    return render_template('show_prediction.html', image_data=img_base64)


@app.route('/parser')
def parser():
    logging.info("Запрос к странице парсера")
    status = get_status(file_path=os.path.join(BASE_DIR, "status", "parser.json"))
    return render_template('parser_page.html', status=status)


@app.route('/ai')
def ai_model():
    logging.info("Запрос к странице ИИ-модели")
    status = get_status(file_path=os.path.join(BASE_DIR, "status", "ai_model.json"))
    countries = get_countries()
    return render_template("ai_page.html", status=status, countries=countries)


@app.route('/ai/quality')
def show_quality():
    country = request.args.get('country')
    img, metrics = get_error(country)
    if type(img) is str and type(metrics) is int:
        return img, metrics
    new_img = io.BytesIO()
    img.save(new_img, format='PNG')
    new_img.seek(0)
    img_base64 = base64.b64encode(new_img.read()).decode('utf-8')
    return render_template('show_quality.html', image_data=img_base64, metrics=metrics)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    DatabasePool.init_pool()
    try:
        app.run(host="0.0.0.0", port=5000)
    except Exception as e:
        logging.error("Ошибка в работе приложения: %s", e)
    finally:
        DatabasePool.close_pool()
