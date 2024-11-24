from flask import Flask

app = Flask(__name__)

@app.route('/parser')
def interface():
    return "This is parser"

if __name__ == '__main__':
    app.run(port=5001)