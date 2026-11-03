"""Authentication helpers for the single-owner private analysis history."""

from dataclasses import dataclass, field
import base64
import binascii
import hashlib
import hmac
import os
import secrets
import time

SESSION_COOKIE = "graph_session"
SESSION_MAX_AGE = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class AuthSettings:
    username: str
    password: str = field(repr=False)
    secret: bytes = field(repr=False)
    enabled: bool
    secure_cookie: bool

    @classmethod
    def from_environment(cls):
        username = os.environ.get("APP_USERNAME", "")
        password = os.environ.get("APP_PASSWORD", "")
        secret_text = os.environ.get("APP_SESSION_SECRET", "")
        enabled = bool(username or password or secret_text)

        if enabled and (not username or not password or not secret_text):
            raise RuntimeError(
                "Configura APP_USERNAME, APP_PASSWORD y APP_SESSION_SECRET juntos."
            )
        if enabled and len(secret_text.encode("utf-8")) < 32:
            raise RuntimeError("APP_SESSION_SECRET debe tener al menos 32 bytes.")
        if enabled and len(password) < 12:
            raise RuntimeError("APP_PASSWORD debe tener al menos 12 caracteres.")

        return cls(
            username=username,
            password=password,
            secret=secret_text.encode("utf-8"),
            enabled=enabled,
            secure_cookie=False,
        )

    def authenticate(self, username, password):
        username_matches = hmac.compare_digest(
            username.encode("utf-8"), self.username.encode("utf-8")
        )
        password_matches = hmac.compare_digest(
            password.encode("utf-8"), self.password.encode("utf-8")
        )
        return username_matches and password_matches

    def create_session(self):
        expires_at = int(time.time()) + SESSION_MAX_AGE
        payload = f"{self.username}|{expires_at}|{secrets.token_urlsafe(16)}"
        encoded_payload = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
        signature = hmac.new(
            self.secret, encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        return f"{encoded_payload}.{signature}"

    def is_valid_session(self, token):
        if not self.enabled or not token or token.count(".") != 1:
            return False
        encoded_payload, supplied_signature = token.split(".", 1)
        expected_signature = hmac.new(
            self.secret, encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return False
        try:
            payload = base64.urlsafe_b64decode(encoded_payload.encode("ascii")).decode("utf-8")
            username, expiry, _nonce = payload.split("|", 2)
            return (
                hmac.compare_digest(username.encode("utf-8"), self.username.encode("utf-8"))
                and int(expiry) > int(time.time())
            )
        except (ValueError, UnicodeDecodeError, binascii.Error):
            return False
