import json
import os

import boto3
import pytest

from app.main import app

localstack_endpoint = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
bucket_name = "my-books"

s3_client = boto3.client("s3", endpoint_url=localstack_endpoint)


def setup_s3():
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

    initial_books = [
        {"id": 1, "title": "Harry Potter", "rating": 5},
        {"id": 2, "title": "The Tempest", "rating": 2},
    ]
    for book in initial_books:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=f"{book['title']}.json",
            Body=json.dumps(book),
        )


@pytest.fixture
def client():
    app.config["TESTING"] = True
    setup_s3()
    with app.test_client() as client:
        yield client


def test_get_books(client):
    response = client.get("/books")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    titles = {book["title"] for book in data}
    assert "Harry Potter" in titles
    assert "The Tempest" in titles


def test_delete_book(client):
    delete_response = client.delete("/books/1")
    assert delete_response.status_code == 200

    get_response = client.get("/books")
    books_list = get_response.get_json()
    assert len(books_list) == 1
    assert not any(book["id"] == 1 for book in books_list)

    response = s3_client.list_objects_v2(Bucket=bucket_name)
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    assert "Harry Potter.json" not in keys
    assert "The Tempest.json" in keys


def test_add_book(client):
    new_book = {"title": "New Book", "rating": 4}
    response = client.post(
        "/books", data=json.dumps(new_book), content_type="application/json"
    )
    assert response.status_code == 201

    get_response = client.get("/books")
    books_list = get_response.get_json()
    assert len(books_list) == 3
    assert any(book["title"] == "New Book" for book in books_list)

    response = s3_client.list_objects_v2(Bucket=bucket_name)
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    assert "New Book.json" in keys
