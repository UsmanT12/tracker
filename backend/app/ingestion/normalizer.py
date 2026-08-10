import re
import unicodedata
from datetime import date, datetime


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).strip()


def safe_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    cleaned = str(value).strip().replace("+", "")
    if cleaned in {"", "-", "—", "--"}:
        return default
    try:
        return int(float(cleaned))
    except ValueError:
        return default


def parse_minutes(value: object) -> int:
    if value is None:
        return 0
    cleaned = str(value).strip()
    if cleaned in {"", "-", "—", "--", "DNP"}:
        return 0
    parts = cleaned.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(float(cleaned) * 60)
    except ValueError:
        return 0


def parse_made_attempted(value: object) -> tuple[int, int]:
    if value is None:
        return 0, 0
    match = re.search(r"(\d+)\s*[-/]\s*(\d+)", str(value))
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def parse_game_date(value: str) -> date:
    cleaned = re.sub(r"\s+", " ", value.replace(",", " ")).strip()
    for pattern in (
        "%A %B %d %Y",
        "%A %b %d %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(cleaned, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported game date: {value!r}")


def is_dnp(row: dict[str, str]) -> tuple[bool, str | None]:
    joined = " ".join(str(value) for value in row.values()).upper()
    reason_match = re.search(r"\b(DNP(?:\s*[-–—:]\s*[^|]+)?)", joined)
    if reason_match:
        return True, reason_match.group(1)
    minutes = row.get("MIN") or row.get("MINUTES")
    return (parse_minutes(minutes) == 0, None)

