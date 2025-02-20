from flask import Flask, Blueprint, render_template
from app.db_pool import DatabasePool
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io

# ai_bp = Blueprint('ai', __name__, url_prefix='/ai')
app = Flask(__name__)


@app.route('/')
def interface():
    conn = DatabasePool.get_connection()
    countryList = []
    try:
        cursor = conn.cursor()
        query = """SELECT cntry_name FROM country ORDER BY cntry_name;"""
        cursor.execute(query)
        countryList = [row[0] for row in cursor.fetchall()]
        cursor.close()
    finally:
        DatabasePool.release_connection(conn)
    return render_template("ai_page.html", countryList=countryList)


# app.register_blueprint(ai_bp)

if __name__ == '__main__':
    DatabasePool.init_pool()
    try:
        app.run(host='0.0.0.0', port=5002)
    except Exception as e:
        DatabasePool.close_pool()
