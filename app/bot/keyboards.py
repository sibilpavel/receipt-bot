from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import Settings
from app.db import Payment
from app.formatting import format_amount, format_dt
from app.links import receipt_url


def open_receipt(s: Settings, payment_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть чек", url=receipt_url(s, payment_id))]
    ])


def receipts_list(s: Settings, payments: list[Payment]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{format_amount(p.amount_kop)}, {format_dt(p.paid_at, s.tz)}",
            url=receipt_url(s, p.id),
        )]
        for p in payments
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
