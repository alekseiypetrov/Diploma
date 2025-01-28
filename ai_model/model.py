from flask import Flask, render_template
from app.db_pool import DatabasePool
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io

app = Flask(__name__)


@app.route('/ai_page')
def interface():
    conn = DatabasePool.get_connection()
    countryList = []
    try:
        cursor = conn.cursor()
        query = """SELECT * FROM country ORDER BY cntry_name;"""
        cursor.execute(query)
        countryList = cursor.fetchall()
        cursor.close()
    finally:
        DatabasePool.release_connection(conn)
    return render_template("ai_page.html", countryList=countryList)


if __name__ == '__main__':
    DatabasePool.init_pool()
    try:
        app.run(host='0.0.0.0', port=5010, debug=False)
    except Exception as e:
        DatabasePool.close_pool()
