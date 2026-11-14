import json
import logging
import re
import time
from pathlib import Path

import segno
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError

from app.bot.keyboards import open_receipt
from app.config import FARE_KOP
from app.db import Payment
from app.formatting import format_amount, format_dt
from app.links import verify_url
from app.security import check_body, check_link

log = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

PAYMENT_ID = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


class PaymentEvent(BaseModel):
    payment_id: str = Field(pattern=PAYMENT_ID.pattern)
    tg_user_id: int
    amount_kop: int = Field(gt=0)
    description: str = Field(default="Оплата", max_length=120)
    paid_at: int | None = None  # unix time от провайдера; иначе берём момент получения


@router.post("/webhook/payment")
async def payment_webhook(request: Request):
    st = request.app.state
    body = await request.body()
    if not check_body(st.settings.webhook_secret, body, request.headers.get("X-Signature", "")):
        raise HTTPException(403, "bad signature")
    try:
        ev = PaymentEvent.model_validate(json.loads(body))
    except (ValueError, ValidationError) as e:
        raise HTTPException(422, f"bad payload: {e}")

    payment = Payment(ev.payment_id, ev.tg_user_id, FARE_KOP,
                      ev.description, ev.paid_at or int(time.time()))
    is_new = await st.db.add_payment(payment)

    if is_new:  # повторный вебхук не должен дублировать уведомление
        try:
            await st.bot.send_message(
                payment.tg_user_id,
                f"Оплата {format_amount(payment.amount_kop)} прошла успешно.",
                reply_markup=open_receipt(st.settings, payment.id),
            )
        except Exception:
            # платёж сохранён, чек доступен через /receipts; провайдеру отвечаем 200
            log.exception("Не удалось отправить уведомление в Telegram")
    return {"ok": True, "duplicate": not is_new}


@router.get("/r/{payment_id}", response_class=HTMLResponse)
async def receipt(request: Request, payment_id: str, sig: str = ""):
    st = request.app.state
    if not check_link(st.settings.link_secret, "receipt", payment_id, sig):
        raise HTTPException(404)
    p = await st.db.get_payment(payment_id)
    if not p:
        raise HTTPException(404)

    qr = segno.make(verify_url(st.settings, p.id), error="m").svg_inline(
        dark="#0e1a2b", light=None, border=0, omitsize=True)
    return templates.TemplateResponse(request, "receipt.html", {
        "amount": format_amount(p.amount_kop),
        "description": p.description,
        "date": format_dt(p.paid_at, st.settings.tz),
        "payment_id": p.id,
        "paid_at": p.paid_at,
        "qr": qr,
        "test_mode": st.settings.test_mode,
    })


@router.get("/verify/{payment_id}", response_class=HTMLResponse)
async def verify(request: Request, payment_id: str, sig: str = ""):
    st = request.app.state
    p = None
    if check_link(st.settings.link_secret, "verify", payment_id, sig):
        p = await st.db.get_payment(payment_id)
    ctx = {"ok": p is not None}
    if p:
        ctx.update(amount=format_amount(p.amount_kop), payment_id=p.id,
                   date=format_dt(p.paid_at, st.settings.tz, seconds=True))
    return templates.TemplateResponse(request, "verify.html", ctx,
                                      status_code=200 if p else 404)
