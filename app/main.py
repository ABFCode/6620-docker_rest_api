import localstack_client.session as boto3
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


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    book_to_delete = next((book for book in books if book["id"] == book_id), None)
    print(f"Deleting book with id: {book_id}, {book_to_delete}")
    if book_to_delete is None:
        return jsonify({"error": "Book not found"}), 404
    books.remove(book_to_delete)
    return jsonify({"message": "Book deleted"}), 200


@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    book_to_update = next((book for book in books if book["id"] == book_id), None)
    print(f"Updating book with id: {book_id}, {book_to_update}")
    if book_to_update is None:
        return jsonify({"error": "Book not found"}), 404

    if "title" in data:
        book_to_update["title"] = data["title"]
    if "rating" in data:
        book_to_update["rating"] = data["rating"]
    return jsonify(book_to_update), 200


client = boto3.client("s3")
response = client.list_buckets()
print(response)
