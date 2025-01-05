import json

import pytest

from adumbra.webserver import app
from adumbra.database.users import UserModel


@pytest.fixture
def client():
    test_client = app.test_client()
    return test_client


@pytest.fixture(autouse=True)
def register_user(client):
    print("BEGIN")
    creds = {"username": "user1", "password": "pass"}
    response = client.post("/api/user/register", json=creds)
    yield json.loads(response.data)
    UserModel.objects.delete()
    print("END")
