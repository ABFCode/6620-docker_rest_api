import pytest
from flask import Response

from app.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_hello(client):
    response: Response = client.get("/")

    assert response.status_code == 200

    assert response.get_data(as_text=True) == "<p>Hello, World!</p>"


def test_get_books(client):
    response: Response = client.get("/books")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["title"] == "Harry Potter"


def test_add_book(client):
    new_book = {"title": "CLRS", "rating": 0.3}
    response: Response = client.post("/books", json=new_book)
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "CLRS"
    assert data["rating"] == 0.3
    get_response = client.get("/books")
    books_list = get_response.get_json()
    assert any(book["title"] == "Harry Potter" for book in books_list)


def test_delete_book(client):
    response: Response = client.get("/books")
    books_list = response.get_json()
    assert any(book["id"] == 1 for book in books_list)

    delete_response: Response = client.delete("/books/1")
    assert delete_response.status_code == 200
    data = delete_response.get_json()
    assert data["message"] == "Book deleted"

    response: Response = client.get("/books")
    books_list = response.get_json()
    assert not any(book["id"] == 1 for book in books_list)

    delete_response = client.delete("/books/111")
    assert delete_response.status_code == 404
    data = delete_response.get_json()
    assert data["error"] == "Book not found"
