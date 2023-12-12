import bcrypt
from backend.database import get_user_hashed_password, get_user_hashed_pin

def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())

def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)


def check_user_password(username: str, password: str):
    return check_password(password, get_user_hashed_password(username))

def check_user_pin(username: str, pin: str):
    user_hashed_pin = get_user_hashed_pin(username)
    if not user_hashed_pin:
        return False
    return check_password(pin, user_hashed_pin)