import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class FakeBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.sent.append((chat_id, text, reply_markup))


@pytest.fixture
def settings(tmp_path):
    return Settings(bot_token="x", base_url="https://pay.test",
                    webhook_secret=b"wh-secret", link_secret=b"link-secret",
                    db_path=str(tmp_path / "t.db"))


@pytest.fixture
def bot():
    return FakeBot()


@pytest.fixture
def client(settings, bot):
    with TestClient(create_app(settings, bot=bot, polling=False)) as c:
        yield c
