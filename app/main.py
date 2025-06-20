from flask import Flask, jsonify, request

app = Flask(__name__)

books = [
    {"id": 1, "title": "Harry Potter", "rating": 5},
    {"id": 2, "title": "The Tempest", "rating": 2},
]


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/books", methods=["GET"])
def get_books():
    return jsonify(books), 200


@app.route("/books", methods=["POST"])
def add_book():
    data = request.get_json()
    if not data or "title" not in data or "rating" not in data:
        return jsonify({"error": "Missing title or rating"}, 400)

    new_id = max(book["id"] for book in books) + 1
    new_book = {"id": new_id, "title": data["title"], "rating": data["rating"]}
    books.append(new_book)
    return jsonify(new_book), 201
