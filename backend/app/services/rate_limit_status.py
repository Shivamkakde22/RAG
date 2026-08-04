import re
import threading
import copy
from datetime import datetime, timezone

_lock = threading.Lock()

_status = {
    "checked_at": None,
    "per_minute": {
        "tokens": None,
        "requests": None,
    },
    "daily": {
        "known": False
    }
}

_DAILY_RE = re.compile(
    r"Limit (\d+), Used (\d+).*?try again in (?:(\d+)m)?([\d.]+)s",
    re.IGNORECASE | re.DOTALL
)

_DURATION_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?$")


def _parse_duration_seconds(text):
    if not text:
        return None

    text = text.strip()
    if text.endswith("ms"):
        try:
            return float(text[:-2]) / 1000
        except ValueError:
            return None

    match = _DURATION_RE.match(text)
    if not match:
        return None

    hours, minutes, seconds = match.groups()
    if not (hours or minutes or seconds):
        return None

    total = 0.0
    if hours:
        total += int(hours) * 3600
    if minutes:
        total += int(minutes) * 60
    if seconds:
        total += float(seconds)
    return total


def record_from_headers(headers):
    if not headers:
        return

    limit_tokens = headers.get("x-ratelimit-limit-tokens")
    remaining_tokens = headers.get("x-ratelimit-remaining-tokens")
    reset_tokens = headers.get("x-ratelimit-reset-tokens")
    limit_requests = headers.get("x-ratelimit-limit-requests")
    remaining_requests = headers.get("x-ratelimit-remaining-requests")
    reset_requests = headers.get("x-ratelimit-reset-requests")

    with _lock:
        if limit_tokens is not None:
            _status["per_minute"]["tokens"] = {
                "limit": int(limit_tokens),
                "remaining": int(remaining_tokens) if remaining_tokens is not None else None,
                "reset_in": reset_tokens,
                "reset_in_seconds": _parse_duration_seconds(reset_tokens),
            }
        if limit_requests is not None:
            _status["per_minute"]["requests"] = {
                "limit": int(limit_requests),
                "remaining": int(remaining_requests) if remaining_requests is not None else None,
                "reset_in": reset_requests,
                "reset_in_seconds": _parse_duration_seconds(reset_requests),
            }
        _status["checked_at"] = datetime.now(timezone.utc).isoformat()


def record_daily_limit(message):
    match = _DAILY_RE.search(message or "")
    if not match:
        return

    limit, used, minutes, seconds = match.groups()
    retry_after_seconds = float(seconds) + (int(minutes) * 60 if minutes else 0)

    with _lock:
        _status["daily"] = {
            "known": True,
            "limit": int(limit),
            "used": int(used),
            "retry_after_seconds": round(retry_after_seconds, 1),
            "hit_at": datetime.now(timezone.utc).isoformat(),
        }


def get_status():
    with _lock:
        return copy.deepcopy(_status)
