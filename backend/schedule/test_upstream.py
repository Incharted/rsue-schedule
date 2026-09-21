from unittest.mock import patch
from urllib.error import URLError
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.core.cache.backends.locmem import LocMemCache
from rest_framework.test import APIClient
from . import upstream


class UniversityTests(SimpleTestCase):
    def test_search_category_heuristic(self):
        self.assertEqual(upstream.entry_category("ИБ-312"), "full-time")
        self.assertEqual(upstream.entry_category("ЭКZ-211"), "part-time")
        self.assertEqual(upstream.entry_category("МЕНOZ-211"), "mixed")
        self.assertEqual(upstream.entry_category("Иванов И. И."), "teacher")
        self.assertIsNone(upstream.entry_category("Служебная запись"))

    def test_dates_and_parallel_subgroups_are_preserved(self):
        lesson = {"id": 1, "subject": "Math", "subgroup": {"name": "1"}}
        data = {
            "instance": "Test",
            "kind": "Group",
            "weeks": [
                {
                    "name": "Odd",
                    "days": [
                        {
                            "date": date,
                            "pairs": [
                                {
                                    "id": 1,
                                    "startTime": "08:30:00",
                                    "endTime": "10:00:00",
                                    "lessons": [
                                        lesson,
                                        {**lesson, "subgroup": {"name": "2"}},
                                    ],
                                }
                            ],
                        }
                    ],
                }
                for date in ["01.09.2026", "15.09.2026"]
            ],
        }
        result = upstream.normalize_schedule(data)
        self.assertEqual(
            [w["start"] for w in result["weeks"]], ["2026-09-01", "2026-09-15"]
        )
        rows = [row for week in result["weeks"] for row in week["lessons"]]
        self.assertEqual(len({row["id"] for row in rows}), 4)
        self.assertEqual(rows[1]["subgroup"], "2")

    def test_fresh_cache_and_stale_fallback(self):
        cache = LocMemCache("university-test", {})
        cache.clear()
        with patch.object(upstream, "cache", cache), patch.object(
            upstream, "urlopen"
        ) as fetch:
            fetch.return_value.__enter__.return_value.read.return_value = (
                b'[{"id":1,"name":"Test"}]'
            )
            first = upstream.fetch_cached("search/", upstream.search_entries)
            self.assertFalse(first["stale"])
            upstream.fetch_cached("search/", upstream.search_entries)
            self.assertEqual(fetch.call_count, 1)
            fetch.side_effect = URLError("offline")
            with patch.object(upstream, "FRESH_SECONDS", -1):
                fallback = upstream.fetch_cached("search/", upstream.search_entries)
            self.assertTrue(fallback["stale"])
            self.assertEqual(first["data"], fallback["data"])
            self.assertEqual(first["updated_at"], fallback["updated_at"])

    def test_endpoint_requires_login_and_handles_unavailable_source(self):
        anonymous = APIClient()
        self.assertEqual(anonymous.get("/api/university/").status_code, 403)

        client = APIClient()
        client.force_authenticate(SimpleNamespace(is_authenticated=True))
        with patch.object(upstream, "fetch_cached", side_effect=URLError("offline")):
            self.assertEqual(client.get("/api/university/").status_code, 502)
        with patch.object(
            upstream, "fetch_cached", return_value={"data": [], "stale": False}
        ):
            self.assertEqual(client.get("/api/university/").status_code, 200)
