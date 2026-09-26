import hashlib
import hmac
import os
import secrets
import time


SESSION_TTL = int(
    os.getenv(
        "SESSION_TTL_SECONDS",
        "3600"
    )
)


_sessions = {}


def hash_password(password):

    salt = secrets.token_bytes(16)


    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000
    )


    return (
        salt.hex()
        + ":"
        + digest.hex()
    )


def verify_password(
    password,
    stored
):

    try:

        salt_hex, digest_hex = stored.split(":")

        salt = bytes.fromhex(
            salt_hex
        )


        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200_000
        )


        return hmac.compare_digest(
            digest.hex(),
            digest_hex
        )

    except Exception:

        return False


def create_session(username):

    token = secrets.token_urlsafe(
        32
    )


    _sessions[token] = {
        "username": username,
        "expires": (
            time.time()
            + SESSION_TTL
        )
    }


    return token


def is_valid_session(token):

    if not token:
        return False


    session = _sessions.get(
        token
    )


    if not session:
        return False


    if session["expires"] < time.time():

        _sessions.pop(
            token,
            None
        )

        return False


    return True