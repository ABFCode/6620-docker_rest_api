import json
import os
from decimal import Decimal

import boto3
from flask import Flask, jsonify, request

app = Flask(__name__)

localstack_endpoint = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
bucket_name = "my-books"
table_name = "books"

s3 = boto3.resource("s3", endpoint_url=localstack_endpoint)
dynamodb = boto3.resource("dynamodb", endpoint_url=localstack_endpoint)
table = dynamodb.Table(table_name)



class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o)
        return super(DecimalEncoder, self).default(o)

app.json_encoder = DecimalEncoder


try:
    if table.item_count == 0:
        print(f"Table '{table_name}' is empty. Populating from books.json")
        with open("books.json", "r") as file:
            data = json.load(file)
            for book in data["books"]:
                item_for_dynamo = json.loads(
                    json.dumps(book), parse_float=Decimal, parse_int=Decimal
                )

                s3.Object(bucket_name, f"book_{book['id']}.json").put(
                    Body=json.dumps(book)
                )
                table.put_item(Item=item_for_dynamo)
except Exception as e:
    print(f"Could not check/populate resources on startup: {e}")


def _get_all_books_from_dynamodb():
    try:
        response = table.scan()
        return response.get("Items", [])
    except Exception as e:
        print(f"Error fetching books from DynamoDB: {e}")
        return []


@app.route("/books", methods=["GET"])
def get_books():
    books = _get_all_books_from_dynamodb()
    return jsonify(books), 200


@app.route("/books", methods=["POST"])
def add_book():
    data = request.get_json()
    if not data or "title" not in data or "rating" not in data:
        return jsonify({"error": "Missing title or rating"}, 400)

    books = _get_all_books_from_dynamodb()
    new_id = max((book["id"] for book in books), default=0) + 1
    
    new_book = {
        "id": new_id,
        "title": data["title"],
        "rating": Decimal(str(data["rating"])),
    }

    s3.Object(bucket_name, f"book_{new_book['id']}.json").put(
        Body=json.dumps(new_book, cls=DecimalEncoder)
    )
    table.put_item(Item=new_book)

    return jsonify(new_book), 201


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    s3.Object(bucket_name, f"book_{book_id}.json").delete()
    table.delete_item(Key={"id": book_id})
    return jsonify({"message": "Book deleted"}), 200


@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    response = table.get_item(Key={"id": book_id})
    if "Item" not in response:
        return jsonify({"error": "Book not found"}), 404

    book_to_update = response["Item"]
    
    if "title" in data:
        book_to_update["title"] = data.get("title")
    if "rating" in data:
        book_to_update["rating"] = Decimal(str(data["rating"]))

    s3.Object(bucket_name, f"book_{book_id}.json").put(
        Body=json.dumps(book_to_update, cls=DecimalEncoder)
    )
    table.put_item(Item=book_to_update)

    return jsonify(book_to_update), 200