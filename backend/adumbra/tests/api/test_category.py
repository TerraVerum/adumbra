import json

import pytest

from adumbra.database import CategoryModel


test_category_data = [
    {"name": "test1"},
    {
        "name": "test2",
        "color": "white",
        "metadata": {"key1": True, "key2": 1, "key3": "value"},
    },
    {"name": "test3", "color": "black"},
]


# Clean categories before each test
@pytest.fixture(scope="function", autouse=True)
def clean_categories():
    CategoryModel.objects.delete()


class TestCategory:

    @pytest.mark.run(before="test_post_categories")
    def test_get_empty(self, client):
        response = client.get("/api/category/")
        data = json.loads(response.data)

        assert isinstance(data, list)
        assert len(data) == 0

    def test_post_no_data(self, client):
        response = client.post("/api/category/")
        assert response.status_code == 400

    @pytest.mark.run(after="test_get_empty")
    def test_post_categories(self, client):
        # Category 1 Test
        data = {"name": "test1"}
        response = client.post("/api/category/", json=data)

        r = json.loads(response.data)
        assert response.status_code == 200
        assert r.get("name") == data.get("name")
        assert r.get("color") is not None
        assert r.get("metadata") is not None
        assert r.get("id") is not None

        # Category 2 Test
        data = {
            "name": "test2",
            "color": "white",
            "metadata": {"key1": True, "key2": 1, "key3": "value"},
        }
        response = client.post("/api/category/", json=data)

        r = json.loads(response.data)
        assert response.status_code == 200
        assert r.get("name") == data.get("name")
        assert r.get("color") == data.get("color")
        assert r.get("metadata") == data.get("metadata")
        assert r.get("id") is not None

    def test_post_categories_invalid(self, client):
        pass

    @pytest.mark.run(after="test_post_categories")
    def test_post_already_existing_category(self, client):
        pass


class TestCategoryId:

    @pytest.fixture
    def generate_categories(self, client):
        post_response = client.post("/api/category/", json=test_category_data[0])
        category1_id = json.loads(post_response.data).get("id")

        post_response = client.post("/api/category/", json=test_category_data[1])
        category2_id = json.loads(post_response.data).get("id")

        post_response = client.post("/api/category/", json=test_category_data[2])
        category3_id = json.loads(post_response.data).get("id")

        return [category1_id, category2_id, category3_id]

    @pytest.mark.run(after="test_post_categories")
    def test_get(self, client, generate_categories):
        category2_id = generate_categories[1]
        response = client.get(f"/api/category/{category2_id}")

        r = json.loads(response.data)
        assert response.status_code == 200
        assert r.get("name") == "test2"
        assert r.get("color") == "white"

    def test_get_invalid_id(self, client):
        response = client.get("/api/category/1000")
        assert response.status_code == 400

    def test_delete_invalid_id(self, client):
        response = client.delete("/api/category/1000")
        assert response.status_code == 400

    @pytest.mark.run(after="test_post_categories")
    def test_delete_category(self, client, generate_categories):
        category3_id = generate_categories[2]
        response = client.delete(f"/api/category/{category3_id}")
        assert response.status_code == 200

    @pytest.mark.run(after="test_post_categories")
    def test_put_equal(self, client, generate_categories):
        """Test response when the name to update is the same as already stored"""
        data = {"name": "test1"}
        category1_id = generate_categories[0]
        response = client.put(f"/api/category/{category1_id}", json=data)
        assert response.status_code == 200

    def test_put_invalid_id(self, client):
        """Test response when id does not exit"""
        response = client.put("/api/category/1000")
        assert response.status_code == 400

    def test_put_not_unique(self, client, generate_categories):
        """Test response when the name already exits"""
        data = {"name": "test2"}
        category1_id = generate_categories[0]
        response = client.put(f"/api/category/{category1_id}", json=data)
        assert response.status_code == 400

    def test_put_empty(self, client, generate_categories):
        """Test response when category name is empty"""
        data = {"name": ""}
        category1_id = generate_categories[0]
        response = client.put(f"/api/category/{category1_id}", json=data)
        assert response.status_code == 400

    @pytest.mark.run(after="test_put_not_unique")
    def test_put(self, client, generate_categories):
        """Test response when update is correct"""
        data = {"name": "test1_updated"}
        category1_id = generate_categories[0]
        response = client.put(f"/api/category/{category1_id}", json=data)
        assert response.status_code == 200

    @pytest.mark.run(after="test_put")
    def test_put_reset(self, client, generate_categories):
        """Reset test after a correct update"""
        data = {"name": "test1"}
        category1_id = generate_categories[0]
        print("category1_id", category1_id)
        response = client.put(f"/api/category/{category1_id}", json=data)
        assert response.status_code == 200


class TestCategoryData:

    # TODO write tests for data
    def test(self):
        pass
