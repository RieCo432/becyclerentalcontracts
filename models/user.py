from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data["_id"]
        self.username = user_data["username"]
        self.admin = user_data["admin"]
        self.depositBearer = user_data["depositBearer"]
        self.rentalChecker = user_data["rentalChecker"]
