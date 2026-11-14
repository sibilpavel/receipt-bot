"""Имитация вебхука провайдера: python scripts/send_test_webhook.py <tg_user_id> [сумма_в_копейках]"""
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request

from dotenv import load_dotenv

load_dotenv()
tg_user_id = int(sys.argv[1])
amount = int(sys.argv[2]) if len(sys.argv) > 2 else 5300

body = json.dumps({
    "payment_id": f"test_{int(time.time())}",
    "tg_user_id": tg_user_id,
    "amount_kop": amount,
    "description": "Тестовый платёж",
}).encode()
sig = hmac.new(os.environ["WEBHOOK_SECRET"].encode(), body, hashlib.sha256).hexdigest()

url = os.getenv("LOCAL_URL", "http://127.0.0.1:8000") + "/webhook/payment"
req = urllib.request.Request(url, data=body, headers={"X-Signature": sig})
print(urllib.request.urlopen(req).read().decode())
