from dataclasses import dataclass
from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id          TEXT PRIMARY KEY,
    tg_user_id  INTEGER NOT NULL,
    amount_kop  INTEGER NOT NULL,
    description TEXT    NOT NULL,
    paid_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments (tg_user_id, paid_at DESC);
"""


@dataclass(frozen=True)
class Payment:
    id: str
    tg_user_id: int
    amount_kop: int
    description: str
    paid_at: int


class Database:
    def __init__(self, path: str):
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    async def add_payment(self, p: Payment) -> bool:
        """True, если платёж новый; False, если это повтор вебхука."""
        cur = await self._conn.execute(
            "INSERT OR IGNORE INTO payments VALUES (?, ?, ?, ?, ?)",
            (p.id, p.tg_user_id, p.amount_kop, p.description, p.paid_at),
        )
        await self._conn.commit()
        return cur.rowcount == 1

    async def get_payment(self, payment_id: str) -> Payment | None:
        cur = await self._conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        row = await cur.fetchone()
        return Payment(*row) if row else None

    async def list_for_user(self, tg_user_id: int, limit: int = 5) -> list[Payment]:
        cur = await self._conn.execute(
            "SELECT * FROM payments WHERE tg_user_id = ? ORDER BY paid_at DESC LIMIT ?",
            (tg_user_id, limit),
        )
        return [Payment(*r) for r in await cur.fetchall()]
