from flask import Flask, jsonify

app = Flask(__name__)

books = [
    {"id": 1, "title": "Harry Potter", "rating": 5},
    {"id": 2, "title": "The Tempest", "rating": 2},
]


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/books", methods=["GET"])
def get_db_items():
    return jsonify(books), 200
