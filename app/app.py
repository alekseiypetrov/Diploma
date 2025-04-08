from flask import Flask, render_template, Response, request
import io
import base64

from db_pool import DatabasePool
from rendering import get_image
from prediction import get_prediction

app = Flask(__name__)


@app.route('/')
def home():
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
    return render_template('index.html', countries=countries)


@app.route('/show_plot', methods=['POST'])
def show_data():
    mode = request.form.get('mode')
    img = get_image(mode)
    if type(img) is str:
        return img, 400
    new_img = io.BytesIO()
    img.save(new_img, format='PNG')
    new_img.seek(0)
    img_base64 = base64.b64encode(new_img.read()).decode('utf-8')
    return render_template('show_plot.html', image_data=img_base64)


@app.route('/prediction', methods=['POST'])
def prediction():
    country = request.form.get('country')
    img = get_prediction(country)
    new_img = io.BytesIO()
    img.save(new_img, format='PNG')
    new_img.seek(0)
    return Response(new_img, mimetype='image/png')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    DatabasePool.init_pool()
    try:
        app.run(host="0.0.0.0", port=5000)
    except Exception as e:
        DatabasePool.close_pool()
