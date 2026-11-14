from datetime import datetime
from zoneinfo import ZoneInfo


def format_amount(kop: int) -> str:
    rub, rest = divmod(kop, 100)
    whole = f"{rub:,}".replace(",", "\u00a0")
    return f"{whole},{rest:02d}\u00a0₽" if rest else f"{whole}\u00a0₽"


def format_dt(ts: int, tz: ZoneInfo, seconds: bool = False) -> str:
    fmt = "%d.%m.%Y %H:%M:%S" if seconds else "%d.%m.%Y %H:%M"
    return datetime.fromtimestamp(ts, tz).strftime(fmt)
