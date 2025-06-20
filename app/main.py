from flask import Flask, jsonify

app = Flask(__name__)

db = [1, 2, 3]


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/db", methods=["GET"])
def get_items():
    return jsonify(db), 200
