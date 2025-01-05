from adumbra.database import UserModel


class TestUser:

    @classmethod
    def setup_class(cls):
        UserModel.objects.delete()

    @classmethod
    def teardown_class(cls):
        UserModel.objects.delete()

    def test_create_first_user(self, register_user):
        data = register_user
        assert data.get("success")

        user = data.get("user")
        assert user.get("is_admin")
