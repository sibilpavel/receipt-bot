import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


FARE_KOP = 5300  # цена проезда всегда 53 ₽


@dataclass(frozen=True)
class Settings:
    bot_token: str
    base_url: str
    webhook_secret: bytes
    link_secret: bytes
    db_path: str = "data/payments.db"
    timezone: str = "Europe/Moscow"
    test_mode: bool = False  # TEST_MODE=1: чек по сообщению "сумма номер" прямо в боте

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            bot_token=os.environ["BOT_TOKEN"],
            base_url=os.environ["BASE_URL"].rstrip("/"),
            webhook_secret=os.environ["WEBHOOK_SECRET"].encode(),
            link_secret=os.environ["LINK_SECRET"].encode(),
            db_path=os.getenv("DB_PATH", "data/payments.db"),
            timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
            test_mode=os.getenv("TEST_MODE", "").lower() in ("1", "true", "yes"),
        )
