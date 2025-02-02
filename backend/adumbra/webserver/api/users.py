import logging
import typing as t

from flask_login import current_user, login_required, login_user, logout_user
from flask_restx import Namespace, Resource, reqparse
from werkzeug.security import check_password_hash, generate_password_hash

from adumbra.config import CONFIG
from adumbra.database import UserModel
from adumbra.util.api_bridge import queryset_to_json

logger = logging.getLogger("gunicorn.error")

api = Namespace("user", description="User related operations")

register = reqparse.RequestParser()
register.add_argument("username", required=True, location="json")
register.add_argument("password", required=True, location="json")
register.add_argument("email", location="json")
register.add_argument("name", location="json")

login = reqparse.RequestParser()
login.add_argument("password", required=True, location="json")
login.add_argument("username", required=True, location="json")

set_password = reqparse.RequestParser()
set_password.add_argument("password", required=True, location="json")
set_password.add_argument("new_password", required=True, location="json")

current_user_model = t.cast(UserModel, current_user)
"""
Flask doesn't type hint the current_user object correctly by default so this explicitly
cast version plays nicer with type checkers.
"""


@api.route("/")
class User(Resource):
    @login_required
    def get(self):
        """Get information of current user"""
        if CONFIG.login_disabled:
            return current_user_model.to_json()
        user_json = queryset_to_json(current_user_model)
        del user_json["password"]

        return {"user": user_json}


@api.route("/password")
class UserPassword(Resource):

    @login_required
    @api.expect(register)
    def post(self):
        """Set password of current user"""
        args = set_password.parse_args()

        if check_password_hash(current_user.password, args.get("password")):
            current_user.update(
                password=generate_password_hash(
                    args.get("new_password"), method="pbkdf2:sha256"
                ),
                new=False,
            )
            return {"success": True}

        return {
            "success": False,
            "message": "Password does not match current passowrd",
        }, 400


@api.route("/register")
class UserRegister(Resource):
    @api.expect(register)
    def post(self):
        """Creates user"""

        users = UserModel.objects.count()

        if not CONFIG.allow_registration and users != 0:
            return {
                "success": False,
                "message": "Registration of new accounts is disabled.",
            }, 400

        args = register.parse_args()
        username = args.get("username")

        if UserModel.objects(username__iexact=username).first():
            return {"success": False, "message": "Username already exists."}, 400

        user = UserModel()
        user.username = args.get("username")
        # user.password = generate_password_hash(args.get('password'), method='sha256')
        user.password = generate_password_hash(
            args.get("password"), method="pbkdf2:sha256"
        )
        user.name = args.get("name")
        user.email = args.get("email")
        if users == 0:
            user.is_admin = True
        user.save()

        login_user(user)

        user_json = queryset_to_json(current_user_model)
        del user_json["password"]

        return {"success": True, "user": user_json}


@api.route("/login")
class UserLogin(Resource):
    @api.expect(login)
    def post(self):
        """Logs user in"""
        args = login.parse_args()
        username = args.get("username")

        user = UserModel.objects(username__iexact=username).first()
        if user is None:
            return {"success": False, "message": "Could not authenticate user"}, 400

        if check_password_hash(user.password, args.get("password")):
            login_user(user)

            user_json = queryset_to_json(current_user_model)
            del user_json["password"]

            logger.info(f"User {current_user.username} has LOGIN")

            return {"success": True, "user": user_json}

        return {"success": False, "message": "Could not authenticate user"}, 400


@api.route("/logout")
class UserLogout(Resource):
    @login_required
    def get(self):
        """Logs user out"""
        logger.info(f"User {current_user.username} has LOGOUT")
        logout_user()
        return {"success": True}
