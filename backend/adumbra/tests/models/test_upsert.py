from adumbra.database import CategoryModel, upsert

category1 = {"name": "Upsert Category", "color": "white"}


class TestCategoryUpsert:

    def test_create_category(self):

        query = {"name": category1.get("name")}
        create_category1 = upsert(CategoryModel, query=query, update=category1)

        assert create_category1.name == category1.get("name")
        assert create_category1.color == category1.get("color")

        found = CategoryModel.objects(**query).first()
        assert found.name == category1.get("name")
        assert found.color == category1.get("color")

    def test_update_category(self):
        query = {"name": category1.get("name")}
        updates = {"name": "Upsert New", "color": "black"}

        found = upsert(CategoryModel, query=query, update=updates)

        assert found.name == updates.get("name")
        assert found.color == updates.get("color")
