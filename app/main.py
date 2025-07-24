import json
import os

import boto3
from flask import Flask, jsonify, request

app = Flask(__name__)


with open("books.json", "r") as file:
    data = json.load(file)


localstack_endpoint = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
bucket_name = "my-books"

s3 = boto3.resource("s3", endpoint_url=localstack_endpoint)
bucket = s3.Bucket(bucket_name)


try:
    if not any(bucket.objects.limit(1)):
        print(f"Bucket '{bucket_name}' is empty. Populating from books.json")
        with open("books.json", "r") as file:
            data = json.load(file)
            for book in data["books"]:
                s3_object = s3.Object(bucket_name, f"{book['title']}.json")
                s3_object.put(Body=json.dumps(book))
except Exception as e:
    print(f"Could not check bucket on startup: {e}")


def _get_all_books_from_s3():
    books = []
    try:
        for book_object in bucket.objects.all():
            book_body = book_object.get()["Body"].read()
            book = json.loads(book_body)
            books.append(book)
    except Exception as e:
        print(f"Error fetching books from s3: {e}")
        return []

    return books


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/books", methods=["GET"])
def get_books():
    books = _get_all_books_from_s3()
    return jsonify(books), 200


@app.route("/books", methods=["POST"])
def add_book():
    data = request.get_json()
    if not data or "title" not in data or "rating" not in data:
        return jsonify({"error": "Missing title or rating"}, 400)
    
    books = _get_all_books_from_s3()

    new_id = max((book["id"] for book in books), default=0) + 1
    new_book = {"id": new_id, "title": data["title"], "rating": data["rating"]}
    books.append(new_book)
    s3_object = s3.Object(bucket_name, f"{new_book['title']}.json")
    s3_object.put(Body=json.dumps(new_book))
    return jsonify(new_book), 201


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    books = _get_all_books_from_s3()
    book_to_delete = next((book for book in books if book["id"] == book_id), None)
    print(f"Deleting book with id: {book_id}, {book_to_delete}")
    if book_to_delete is None:
        return jsonify({"error": "Book not found"}), 404
    books.remove(book_to_delete)

    s3_object = s3.Object(bucket_name, f"{book_to_delete['title']}.json")
    s3_object.delete()
    return jsonify({"message": "Book deleted"}), 200


@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    books = _get_all_books_from_s3()
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    book_to_update = next((book for book in books if book["id"] == book_id), None)
    print(f"Updating book with id: {book_id}, {book_to_update}")
    if book_to_update is None:
        return jsonify({"error": "Book not found"}), 404

    old_title = book_to_update["title"]
    old_s3_key = f"{old_title}.json"

    if "title" in data:
        book_to_update["title"] = data["title"]
    if "rating" in data:
        book_to_update["rating"] = data["rating"]

    new_s3_key = f"{book_to_update['title']}.json"

    if new_s3_key != old_s3_key:
        print("Deleting old object as title changed")
        s3.Object(bucket_name, old_s3_key).delete()

    s3.Object(bucket_name, new_s3_key).put(Body=json.dumps(book_to_update))

    return jsonify(book_to_update), 200
