from flask_login import AnonymousUserMixin, LoginManager
from werkzeug.security import check_password_hash

from adumbra.database import (
    AnnotationModel,
    CategoryModel,
    DatasetModel,
    ImageModel,
    UserModel,
)

login_manager = LoginManager()


class AnonymousUser(AnonymousUserMixin):
    @property
    def datasets(self):
        return DatasetModel.objects

    @property
    def categories(self):
        return CategoryModel.objects

    @property
    def annotations(self):
        return AnnotationModel.objects

    @property
    def images(self):
        return ImageModel.objects

    @property
    def username(self):
        return "anonymous"

    @property
    def name(self):
        return "Anonymous User"

    @property
    def is_admin(self):
        return False

    def update(self, *args, **kwargs):
        pass

    def to_json(self):
        return {
            "admin": False,
            "username": self.username,
            "name": self.name,
            "is_admin": self.is_admin,
            "anonymous": True,
        }

    def can_edit(self):
        return True

    def can_view(self):
        return True

    def can_download(self):
        return True

    def can_delete(self):
        return True


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return UserModel.objects(id=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    return {"success": False, "message": "Authorization required"}, 401


@login_manager.request_loader
def load_user_from_request(request):
    auth = request.authorization
    if not auth:
        return None
    user = UserModel.objects(username__iexact=auth.username).first()
    if user and check_password_hash(user.password, auth.password):
        # login_user(user)
        return user
    return None
