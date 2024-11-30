from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)


@app.route('/')
def home():
    return render_template('index.html')
    # return 'Hello, World!'


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")
