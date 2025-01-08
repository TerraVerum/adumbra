# Redefining the name is by definition how fixtures work
# pylint: disable=redefined-outer-name
import json

import pytest

# This must be imported before the database models
from adumbra.webserver import app  # isort:skip

from adumbra.database.users import UserModel  # isort:skip


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
