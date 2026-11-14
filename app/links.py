from urllib.parse import quote

from app.config import Settings
from app.security import sign_link


def receipt_url(s: Settings, payment_id: str) -> str:
    sig = sign_link(s.link_secret, "receipt", payment_id)
    return f"{s.base_url}/r/{quote(payment_id)}?sig={sig}"


def verify_url(s: Settings, payment_id: str) -> str:
    sig = sign_link(s.link_secret, "verify", payment_id)
    return f"{s.base_url}/verify/{quote(payment_id)}?sig={sig}"
