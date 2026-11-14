"""Подписи: вебхук от провайдера и ссылки на чек / проверку."""
import hashlib
import hmac


def sign_body(secret: bytes, body: bytes) -> str:
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def check_body(secret: bytes, body: bytes, given: str) -> bool:
    return hmac.compare_digest(sign_body(secret, body), given or "")


def sign_link(secret: bytes, purpose: str, payment_id: str) -> str:
    """purpose разделяет ссылки: подпись для чека не подойдёт для проверки."""
    msg = f"{purpose}:{payment_id}".encode()
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()[:24]


def check_link(secret: bytes, purpose: str, payment_id: str, sig: str) -> bool:
    return hmac.compare_digest(sign_link(secret, purpose, payment_id), sig or "")
