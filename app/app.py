from flask import Flask, render_template, Response, request
from db_pool import DatabasePool
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io
import datetime
import re

app = Flask(__name__)

DATE_FORMAT_REGEX = r"^\d{4}-(0[1-9]|1[0-2])$"


@app.route('/')
def home():
    return render_template('index.html')


# генерация изображения для заданной страны
def generate_img(id_cntry, cntry_name, mode):
    conn = DatabasePool.get_connection()
    try:
        cursor = conn.cursor()
        if mode == "annual":
            query = """SELECT 
            DATE_PART('Year', dte) AS dte_year,
            AVG(temperature) AS avg_year_temp, 
            AVG(new_cases) AS avg_year_cases
            FROM information
            WHERE id_cntry = %s
            GROUP BY dte_year
            
            UNION ALL
            
            SELECT dte_year, avg_year_temp, avg_year_cases
            FROM avg_year_info 
            WHERE id_cntry = %s
            ORDER BY dte_year;"""
            cursor.execute(query, (id_cntry, id_cntry))
        else:
            end_date = datetime.date.today()
            start_date = datetime.date(end_date.year - 2, 1, 1)
            if mode == "range":
                start_date = datetime.datetime.strptime(request.form.get('start_date'), "%Y-%m").date()
                end_date = datetime.datetime.strptime(request.form.get('end_date'), "%Y-%m").date()
                if start_date > end_date:
                    start_date, end_date = end_date, start_date

            query = """SELECT dte, temperature, new_cases FROM information 
            WHERE (id_cntry = %s) AND dte BETWEEN %s AND %s
            ORDER BY dte;"""
            cursor.execute(query, (id_cntry, start_date, end_date))
        dataset = pd.DataFrame(cursor.fetchall(), columns=["dte", "temperature", "new_cases"])
        cursor.close()
    finally:
        DatabasePool.release_connection(conn)

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    axes[0].grid(True)
    axes[0].plot(dataset["dte"], dataset["temperature"])
    axes[0].set_ylabel("Температура")
    for label in axes[0].get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")

    axes[1].grid(True)
    axes[1].plot(dataset["dte"], dataset["new_cases"])
    axes[1].set_ylabel("Новые случаи заболеваемости")
    for label in axes[1].get_xticklabels():
        label.set_rotation(45)
        label.set_ha("right")
    if mode == "annual":
        axes[0].set_xticks(dataset["dte"])
        axes[1].set_xticks(dataset["dte"])

    fig.tight_layout()

    fig.suptitle(f"Изменение температуры и заболеваемости (Страна: {cntry_name})\n\n", fontsize=16)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return Image.open(img)


# "склеивание" изображений
def combine_img(images):
    widths, heights = zip(*(img.size for img in images))
    total_width = max(widths)
    total_height = sum(heights)
    combined_image = Image.new('RGB', (total_width, total_height))
    y_offset = 0
    for img in images:
        combined_image.paste(img, (0, y_offset))
        y_offset += img.height
    return combined_image


@app.route('/show_plot', methods=['POST'])
def show_data():
    mode = request.form.get('mode')
    if mode == "range":
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if not re.match(DATE_FORMAT_REGEX, start_date):
            return f"Ошибка: Начальная дата '{start_date}' не соответствует формату YYYY-MM."
        if not re.match(DATE_FORMAT_REGEX, end_date):
            return f"Ошибка: Конечная дата '{end_date}' не соответствует формату YYYY-MM."
        elif not start_date or not end_date:
            return f"Заполните все поля"

    conn = DatabasePool.get_connection()
    try:
        cursor = conn.cursor()
        query = """SELECT * FROM country ORDER BY cntry_name;"""
        cursor.execute(query)
        images = [
            generate_img(*line, mode) for line in cursor.fetchall()
        ]
        cursor.close()
    finally:
        DatabasePool.release_connection(conn)

    if not images:
        return f"База данных пока пуста"
    combined_image = combine_img(images)
    new_img = io.BytesIO()
    combined_image.save(new_img, format='PNG')
    new_img.seek(0)
    return Response(new_img, mimetype='image/png')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    DatabasePool.init_pool()
    try:
        app.run(debug=False, host="0.0.0.0")
    except Exception as e:
        DatabasePool.close_pool()
