import json
import os
from decimal import Decimal

import boto3
import pytest

from app.main import app

localstack_endpoint = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
bucket_name = "my-books"
table_name = "books"

s3_client = boto3.client("s3", endpoint_url=localstack_endpoint)
dynamodb_resource = boto3.resource("dynamodb", endpoint_url=localstack_endpoint)
dynamodb_table = dynamodb_resource.Table(table_name)


def setup_data():
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

    scan = dynamodb_table.scan()
    with dynamodb_table.batch_writer() as batch:
        for each in scan["Items"]:
            batch.delete_item(Key={"id": each["id"]})

    initial_books = [
        {"id": 1, "title": "Harry Potter", "rating": 5},
        {"id": 2, "title": "The Tempest", "rating": 2},
    ]
    for book in initial_books:
        s3_client.put_object(
            Bucket=bucket_name, Key=f"book_{book['id']}.json", Body=json.dumps(book)
        )
        item_for_dynamo = json.loads(
            json.dumps(book), parse_float=Decimal, parse_int=Decimal
        )
        dynamodb_table.put_item(Item=item_for_dynamo)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    setup_data()
    with app.test_client() as client:
        yield client



def test_get_books(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_get_books_empty(client):
    setup_data()
    scan = dynamodb_table.scan()
    with dynamodb_table.batch_writer() as batch:
        for each in scan["Items"]:
            batch.delete_item(Key={"id": each["id"]})
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

    response = client.get("/books")
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_books_with_ignored_parameters(client):
    response = client.get("/books?author=shakespeare")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_add_book(client):
    new_book_data = {"title": "New Book", "rating": 4}
    response = client.post(
        "/books", data=json.dumps(new_book_data), content_type="application/json"
    )
    assert response.status_code == 201
    assert int(response.get_json()["id"]) == 3
    db_item = dynamodb_table.get_item(Key={"id": 3})["Item"]
    assert db_item["title"] == "New Book"


def test_add_duplicate_book(client):
    book_data = {"title": "Duplicate Book", "rating": 3}
    response1 = client.post(
        "/books", data=json.dumps(book_data), content_type="application/json"
    )
    assert response1.status_code == 201
    assert int(response1.get_json()["id"]) == 3

    response2 = client.post(
        "/books", data=json.dumps(book_data), content_type="application/json"
    )
    assert response2.status_code == 201
    assert int(response2.get_json()["id"]) == 4

    get_response = client.get("/books")
    assert len(get_response.get_json()) == 4


def test_update_book(client):
    update_data = {"title": "New Title", "rating": 1}
    response = client.put(
        "/books/1", data=json.dumps(update_data), content_type="application/json"
    )
    assert response.status_code == 200
    db_item = dynamodb_table.get_item(Key={"id": 1})["Item"]
    assert db_item["title"] == "New Title"


def test_update_nonexistent_book(client):
    response = client.put(
        "/books/999",
        data=json.dumps({"title": "Ghost"}),
        content_type="application/json",
    )
    assert response.status_code == 404


def test_delete_book(client):
    delete_response = client.delete("/books/1")
    assert delete_response.status_code == 200
    with pytest.raises(KeyError):
        dynamodb_table.get_item(Key={"id": 1})["Item"]
    with pytest.raises(s3_client.exceptions.NoSuchKey):
        s3_client.get_object(Bucket=bucket_name, Key="book_1.json")


def test_delete_nonexistent_book(client):
    response = client.delete("/books/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Book not found"