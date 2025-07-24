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
            Key=f"book_{book['id']}.json",
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


def test_add_book(client):
    new_book_data = {"title": "New Book", "rating": 4}
    response = client.post(
        "/books", data=json.dumps(new_book_data), content_type="application/json"
    )
    assert response.status_code == 201
    new_book = response.get_json()
    assert new_book["id"] == 3 

    get_response = client.get("/books")
    books_list = get_response.get_json()
    assert len(books_list) == 3
    assert any(book["title"] == "New Book" for book in books_list)

    response = s3_client.list_objects_v2(Bucket=bucket_name)
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    assert f"book_{new_book['id']}.json" in keys


def test_add_duplicate_book(client):
    book_data = {"title": "Duplicate Book", "rating": 3}
    response1 = client.post(
        "/books", data=json.dumps(book_data), content_type="application/json"
    )
    assert response1.status_code == 201
    assert response1.get_json()["id"] == 3

    response2 = client.post(
        "/books", data=json.dumps(book_data), content_type="application/json"
    )
    assert response2.status_code == 201
    assert response2.get_json()["id"] == 4

    get_response = client.get("/books")
    books_list = get_response.get_json()
    assert len(books_list) == 4

    response = s3_client.list_objects_v2(Bucket=bucket_name)
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    assert "book_3.json" in keys
    assert "book_4.json" in keys


def test_update_book(client):
    update_data = {"title": "New Title", "rating": 1}
    response = client.put(
        "/books/1", data=json.dumps(update_data), content_type="application/json"
    )
    assert response.status_code == 200
    updated_book = response.get_json()
    assert updated_book["title"] == "New Title"

    s3_object = s3_client.get_object(Bucket=bucket_name, Key="book_1.json")
    s3_content = json.loads(s3_object["Body"].read().decode("utf-8"))
    assert s3_content["title"] == "New Title"
    assert s3_content["rating"] == 1


def test_delete_book(client):
    delete_response = client.delete("/books/1")
    assert delete_response.status_code == 200

    get_response = client.get("/books")
    books_list = get_response.get_json()
    assert len(books_list) == 1
    assert not any(book["id"] == 1 for book in books_list)

    response = s3_client.list_objects_v2(Bucket=bucket_name)
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    assert "book_1.json" not in keys
    assert "book_2.json" in keys

def test_get_books_empty(client):
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
    response = client.get("/books")
    assert response.status_code == 200
    assert response.get_json() == []

def test_update_nonexistent_book(client):
    update_data = {"title": "Ghost Book", "rating": 5}
    response = client.put(
        "/books/999",
        data=json.dumps(update_data),
        content_type="application/json",
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Book not found"

def test_delete_nonexistent_book(client):
    response = client.delete("/books/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Book not found"

def test_get_books_with_ignored_parameters(client):
    response = client.get("/books?author=shakespeare")
    assert response.status_code == 200
    assert len(response.get_json()) == 2