from flask import Flask, render_template, Response
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from config import Config
import pandas as pd
import matplotlib.pyplot as plt
import io

db = SQLAlchemy()
app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)


@app.route('/')
def home():
    return render_template('index.html')
    # return 'Hello, World!'


@app.route('/show_plot', methods=['POST'])
def show_data():
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    cursor = conn.cursor()
    query = """SELECT * FROM country ORDER BY cntry_name;"""
    cursor.execute(query)
    countries = pd.DataFrame(cursor.fetchall(), columns=["id_cntry", "cntry_name"])
    m, n = countries.shape

    fig, axes = plt.subplots(m, n, figsize=(12, 6))

    for i, line in enumerate(countries.values):
        id_cntry, cntry_name = line
        query = """SELECT dte, temperature, new_cases FROM information WHERE id_cntry = %s ORDER BY dte;"""
        cursor.execute(query, (id_cntry,))
        dataset = pd.DataFrame(cursor.fetchall(), columns=["dte", "temperature", "new_cases"])
        if axes.ndim == 1:
            axes[0].grid()
            axes[0].set_title(f"Страна: {cntry_name}")
            axes[0].plot(dataset["dte"], dataset["temperature"])

            axes[1].grid()
            axes[1].plot(dataset["dte"], dataset["new_cases"])

        else:
            axes[i, 0].grid()
            axes[i, 0].set_title(f"Страна: {cntry_name}")
            axes[i, 0].plot(dataset["dte"], dataset["temperature"])

            axes[i, 1].grid()
            axes[i, 1].plot(dataset["dte"], dataset["new_cases"])

    cursor.close()
    conn.close()

    fig.suptitle("Изменение температуры и заболеваемости по странам", fontsize=16)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return Response(img, mimetype='image/png')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")
