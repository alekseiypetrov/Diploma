from flask import Flask, Blueprint, render_template
from app.db_pool import DatabasePool
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler import scheduled_learn, log
import logging


# ai_bp = Blueprint('ai', __name__, url_prefix='/ai')
app = Flask(__name__)
scheduler_learn = BackgroundScheduler()
scheduler_learn.add_job(scheduled_learn, 'interval', minutes=10)


@app.route('/')
def interface():
    logging.info("Запрос к странице ИИ-модели")
    return render_template("ai_page.html", log=log)


# app.register_blueprint(ai_bp)

if __name__ == '__main__':
    DatabasePool.init_pool()
    try:
        app.run(host='0.0.0.0', port=5002)
    except Exception as e:
        DatabasePool.close_pool()
