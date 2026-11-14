import re
import time
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import open_receipt, receipts_list
from app.config import Settings
from app.db import Database, Payment
from app.formatting import format_amount

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Здесь появятся чеки по вашим платежам.\n"
        "Последние пять: /receipts"
    )


@router.message(Command("receipts"))
async def receipts(message: Message, db: Database, settings: Settings):
    payments = await db.list_for_user(message.from_user.id, limit=5)
    if not payments:
        await message.answer("Платежей пока нет. Чек придёт сюда сразу после оплаты.")
        return
    await message.answer("Последние платежи:", reply_markup=receipts_list(settings, payments))


# Тестовый режим: "5 12345" -> сумма 5 ₽, номер платежа 12345.
# Сумма в рублях (можно "5,50"), номер — буквы/цифры/_/-.
TEST_INPUT = re.compile(r"^\s*(\d{1,9}(?:[.,]\d{1,2})?)\s+([A-Za-z0-9_\-]{1,64})\s*$")


def parse_test_input(text: str) -> tuple[int, str] | None:
    m = TEST_INPUT.match(text or "")
    if not m:
        return None
    kop = int(Decimal(m.group(1).replace(",", ".")) * 100)
    return (kop, m.group(2)) if kop > 0 else None


@router.message(F.text.regexp(TEST_INPUT))
async def test_payment(message: Message, db: Database, settings: Settings):
    if not settings.test_mode:
        return
    parsed = parse_test_input(message.text)
    if not parsed:
        return
    kop, payment_id = parsed
    # Повторный ввод того же номера не меняет платёж — просто отдаём ту же ссылку.
    await db.add_payment(Payment(payment_id, message.from_user.id, kop,
                                 "Тестовый платёж", int(time.time())))
    p = await db.get_payment(payment_id)
    if p.tg_user_id != message.from_user.id:
        await message.answer("Этот номер платежа уже занят другим пользователем.")
        return
    await message.answer(
        f"Оплата {format_amount(p.amount_kop)} прошла успешно.",
        reply_markup=open_receipt(settings, p.id),
    )
