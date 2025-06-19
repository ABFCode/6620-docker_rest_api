import pytest
from flask import Response

from app.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get(client):
    response: Response = client.get("/")

    assert response.status_code == 200

    assert response.get_data(as_text=True) == "<p>Hello, World!</p>"
