from flask import Flask

app = Flask(__name__)


@app.route('/ai')
def interface():
    return "This is ai"


if __name__ == '__main__':
    app.run(port=5002)
