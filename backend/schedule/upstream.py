"""Read-only adapter for the public RSUE timetable, with last-good caching."""

import hashlib
import json
import ssl
import truststore
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache.backends.filebased import FileBasedCache
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

BASE_URL = "https://rasp-api.rsue.ru/api/v1/schedule/"
cache = FileBasedCache(
    str(settings.BASE_DIR / ".rsue-cache"), {"OPTIONS": {"MAX_ENTRIES": 4000}}
)
FRESH_SECONDS = 900
KEEP_SECONDS = 7 * 86400


def normalize_schedule(data):
    weeks = []
    for week in data["weeks"]:
        dates, lessons = [], []
        for day in week["days"]:
            if not day.get("date"):
                continue
            date = datetime.strptime(day["date"], "%d.%m.%Y").date()
            dates.append(date.isoformat())
            for pair in day["pairs"]:
                for index, lesson in enumerate(pair["lessons"]):
                    lessons.append(
                        {
                            "id": f"{date}:{pair['id']}:{lesson['id']}:{index}",
                            "date": date.isoformat(),
                            "day_of_week": date.isoweekday(),
                            "start_time": pair["startTime"],
                            "end_time": pair["endTime"],
                            "subject_name": lesson["subject"],
                            "teacher_name": (lesson.get("teacher") or {}).get(
                                "name", ""
                            ),
                            "group_name": lesson.get("group", ""),
                            "classroom_number": lesson.get("audience") or "Не указана",
                            "kind": (lesson.get("kind") or {}).get("name", ""),
                            "subgroup": (lesson.get("subgroup") or {}).get("name", ""),
                        }
                    )
        if dates:
            weeks.append(
                {
                    "id": min(dates),
                    "name": week["name"],
                    "start": min(dates),
                    "end": max(dates),
                    "lessons": lessons,
                }
            )
    return {"instance": data["instance"], "kind": data["kind"], "weeks": weeks}


def fetch_cached(path, transform):
    key = hashlib.sha256(path.encode()).hexdigest()
    previous = cache.get(key)
    now = timezone.now()
    if previous and now.timestamp() - previous["timestamp"] < FRESH_SECONDS:
        return {**previous, "stale": False}
    try:
        request = Request(
            BASE_URL + path,
            headers={
                "Accept": "application/json",
                "User-Agent": "RSUE-Schedule-Student-Portal/1.0",
            },
        )
        with urlopen(
            request, timeout=12, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ) as response:
            data = transform(json.load(response))
        result = {
            "data": data,
            "timestamp": now.timestamp(),
            "updated_at": now.isoformat(),
        }
        cache.set(key, result, KEEP_SECONDS)
        return {**result, "stale": False}
    except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
        if previous:
            return {**previous, "stale": True}
        raise


def search_entries(data):
    if not isinstance(data, list):
        raise ValueError("Unexpected search response")
    return [{"id": row["id"], "name": row["name"]} for row in data]


def entry_category(name):
    """The upstream search has no type field, so keep the heuristic isolated."""
    import re

    value = name.strip()
    group = re.fullmatch(r"([А-ЯЁA-Z]+)-\d+", value, re.IGNORECASE)
    if group:
        prefix = group.group(1).upper()
        if re.search(r"[OО][ZЗ]S?$", prefix):
            return "mixed"
        if re.search(r"[ZЗ]S?$", prefix):
            return "part-time"
        return "full-time"
    if re.fullmatch(
        r"[А-ЯЁ][А-ЯЁа-яё-]+\s+[А-ЯЁA-Z]\s*\.\s*[А-ЯЁA-Z]\s*\.", value, re.IGNORECASE
    ):
        return "teacher"
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def university_schedule(request):
    name = request.query_params.get("name", "").strip()
    if len(name) > 150:
        return Response({"detail": "Слишком длинное название."}, status=400)
    try:
        result = fetch_cached(
            "lessons/" + quote(name, safe="") if name else "search/",
            normalize_schedule if name else search_entries,
        )
    except HTTPError as error:
        return Response(
            {
                "detail": (
                    "Расписание не найдено."
                    if error.code == 404
                    else "Сайт университета временно недоступен."
                )
            },
            status=404 if error.code == 404 else 502,
        )
    except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
        return Response(
            {
                "detail": "Не удалось загрузить расписание университета. Попробуйте позже."
            },
            status=502,
        )
    return Response({key: value for key, value in result.items() if key != "timestamp"})
