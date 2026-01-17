import base64
import hashlib
import secrets


ALLOWED_API_KEY_ROLES = {"admin", "runner", "readonly"}


def generate_api_key() -> str:
    token = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(token).decode("utf-8").rstrip("=")


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
