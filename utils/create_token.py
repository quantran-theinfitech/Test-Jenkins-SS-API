import secrets
import string


def create_token(token_length: int):
    characters = string.ascii_letters + string.digits

    token = "".join(secrets.choice(characters) for _ in range(token_length))

    return token
