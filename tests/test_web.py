import json
import re

from app.links import receipt_url, verify_url
from app.security import sign_body

EVENT = {"payment_id": "pay_0001", "tg_user_id": 42, "amount_kop": 5300,
         "description": "Оплата услуги"}


def post(client, payload, secret=b"wh-secret"):
    body = json.dumps(payload).encode()
    return client.post("/webhook/payment", content=body,
                       headers={"X-Signature": sign_body(secret, body)})


def path(url):
    return url.replace("https://pay.test", "")


def test_bad_signature_rejected(client):
    assert post(client, EVENT, secret=b"wrong").status_code == 403


def test_invalid_payload_rejected(client):
    assert post(client, {**EVENT, "amount_kop": 0}).status_code == 422
    assert post(client, {**EVENT, "payment_id": "../x"}).status_code == 422


def test_webhook_notifies_once(client, bot):
    assert post(client, EVENT).json() == {"ok": True, "duplicate": False}
    assert post(client, EVENT).json() == {"ok": True, "duplicate": True}
    assert len(bot.sent) == 1
    assert bot.sent[0][0] == 42


def test_receipt_page(client, settings):
    post(client, EVENT)
    r = client.get(path(receipt_url(settings, "pay_0001")))
    assert r.status_code == 200
    assert "53\u00a0₽" in r.text and "pay_0001" in r.text and "<svg" in r.text


def test_receipt_requires_valid_sig(client):
    post(client, EVENT)
    assert client.get("/r/pay_0001").status_code == 404
    assert client.get("/r/pay_0001?sig=deadbeef").status_code == 404


def test_verify_ok_and_unknown(client, settings):
    post(client, EVENT)
    assert client.get(path(verify_url(settings, "pay_0001"))).status_code == 200
    assert client.get(path(verify_url(settings, "pay_9999"))).status_code == 404
    # подпись от чека не подходит для проверки
    sig = re.search(r"sig=(\w+)", receipt_url(settings, "pay_0001")).group(1)
    assert client.get(f"/verify/pay_0001?sig={sig}").status_code == 404
