from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from .models import Classroom, Lesson
from rest_framework.test import APITransactionTestCase


class ScheduleAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_schedule", verbosity=0)
        cls.admin_user = User.objects.create_user(
            username="test-admin", password="A-test-password-593!", is_staff=True
        )

    def setUp(self):
        self.client.force_authenticate(self.admin_user)

    def test_lists(self):
        for endpoint, count in [
            ("groups", 12),
            ("teachers", 16),
            ("subjects", 18),
            ("buildings", 5),
            ("classrooms", 19),
            ("lessons", 218),
        ]:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(f"/api/{endpoint}/")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.data), count)

    def test_combined_filters_and_display_fields(self):
        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        response = self.client.get(
            "/api/lessons/",
            {
                "group": lesson.group_id,
                "day_of_week": 1,
                "week_type": "odd",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["subject_name"], lesson.subject.name)
        self.assertEqual(
            response.data[0]["building_name"], lesson.classroom.building.name
        )
        self.assertTrue(all(row["group"] == lesson.group_id for row in response.data))

    def test_each_filter(self):
        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        for key, value in [
            ("group", lesson.group_id),
            ("day_of_week", 3),
            ("week_type", "even"),
        ]:
            response = self.client.get("/api/lessons/", {key: value})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data)
            self.assertTrue(all(row[key] == value for row in response.data))

    def test_invalid_filters(self):
        for params in [{"group": "abc"}, {"day_of_week": 8}, {"week_type": "weekly"}]:
            self.assertEqual(self.client.get("/api/lessons/", params).status_code, 400)
        self.assertEqual(self.client.get("/api/lessons/", {"group": 999999}).data, [])

    def payload(self):
        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        return dict(
            group=lesson.group_id,
            teacher=lesson.teacher_id,
            subject=lesson.subject_id,
            classroom=lesson.classroom_id,
            day_of_week=2,
            week_type="even",
            start_time="13:00:00",
            end_time="14:30:00",
        )

    def test_create_lesson(self):
        response = self.client.post("/api/lessons/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(
            Lesson.objects.filter(pk=response.data["id"], day_of_week=2).exists()
        )

    def test_invalid_lesson(self):
        for changes in [
            {"end_time": "12:00:00"},
            {"end_time": "13:00:00"},
            {"group": 999999},
            {"day_of_week": 0},
            {"week_type": "all"},
        ]:
            payload = self.payload() | changes
            self.assertEqual(
                self.client.post("/api/lessons/", payload, format="json").status_code,
                400,
            )
        self.assertEqual(Lesson.objects.count(), 218)

    def test_reference_lists_are_read_only(self):
        self.assertEqual(
            self.client.post("/api/groups/", {"name": "test"}).status_code, 405
        )

    def test_seed_is_repeatable(self):
        call_command("seed_schedule", verbosity=0)
        self.assertEqual(Lesson.objects.count(), 218)

    def test_campus_conflict_on_create_and_patch(self):
        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        other_room = Classroom.objects.get(
            building__name="Факультет менеджмента и предпринимательства", number="305"
        )
        payload = self.payload() | {
            "day_of_week": 1,
            "week_type": "odd",
            "classroom": other_room.pk,
        }
        response = self.client.post("/api/lessons/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("classroom", response.data)
        self.assertEqual(
            self.client.patch(
                f"/api/lessons/{lesson.pk}/",
                {"classroom": other_room.pk},
                format="json",
            ).status_code,
            400,
        )
        lesson.refresh_from_db()
        self.assertNotEqual(lesson.classroom_id, other_room.pk)

    def test_different_campus_allowed_on_other_week_or_day(self):
        payload = self.payload() | {"day_of_week": 4, "week_type": "odd"}
        # Thursday odd is in building 2; Thursday even can independently use main building.
        self.assertEqual(
            self.client.post("/api/lessons/", payload, format="json").status_code, 400
        )
        payload["week_type"] = "even"
        self.assertEqual(
            self.client.post("/api/lessons/", payload, format="json").status_code, 400
        )
        payload["day_of_week"] = 7
        self.assertEqual(
            self.client.post("/api/lessons/", payload, format="json").status_code, 201
        )
        payload.update(
            week_type="odd",
            classroom=Classroom.objects.get(
                building__name="Факультет менеджмента и предпринимательства",
                number="305",
            ).pk,
        )
        self.assertEqual(
            self.client.post("/api/lessons/", payload, format="json").status_code, 201
        )

    def test_seed_groups_stay_in_one_campus_per_day(self):
        from django.db.models import Count

        conflicts = (
            Lesson.objects.values("group_id", "day_of_week", "week_type")
            .annotate(campuses=Count("classroom__building", distinct=True))
            .filter(campuses__gt=1)
        )
        self.assertFalse(conflicts.exists())

    def test_admin_model_validation_rejects_campus_conflict(self):
        from django.core.exceptions import ValidationError

        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        lesson.classroom = Classroom.objects.get(
            building__name="Факультет менеджмента и предпринимательства", number="305"
        )
        with self.assertRaises(ValidationError):
            lesson.full_clean()

    def test_database_constraints(self):
        classroom = Classroom.objects.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Classroom.objects.create(
                building=classroom.building, number=classroom.number
            )
        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        for changes in [
            {"end_time": lesson.start_time},
            {"day_of_week": 8},
            {"week_type": "all"},
        ]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Lesson.objects.filter(pk=lesson.pk).update(**changes)


class AccountTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_schedule", verbosity=0)
        cls.admin = User.objects.create_user(
            username="administrator", password="Test-pass-9182!", is_staff=True
        )
        cls.student = User.objects.create_user(
            username="student", password="Test-pass-9182!", email="student@example.test"
        )

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def token(self):
        return self.client.get("/api/auth/session/").json()["csrfToken"]

    def login_as(self, username="student"):
        return self.client.post(
            "/api/auth/login/",
            {"username": username, "password": "Test-pass-9182!", "remember": True},
            format="json",
            HTTP_X_CSRFTOKEN=self.token(),
        )

    def test_anonymous_cannot_read_or_write_schedule(self):
        self.assertEqual(self.client.get("/api/lessons/").status_code, 403)
        self.assertEqual(
            self.client.post("/api/lessons/", {}, format="json").status_code, 403
        )

    def test_registration_hashes_password_and_never_grants_admin(self):
        payload = dict(
            username="new-student",
            full_name="Новый студент",
            email="new@example.test",
            password1="A-different-password-991!",
            password2="A-different-password-991!",
            is_staff=True,
            is_superuser=True,
        )
        response = self.client.post(
            "/api/auth/register/", payload, format="json", HTTP_X_CSRFTOKEN=self.token()
        )
        self.assertEqual(response.status_code, 201, response.json())
        user = User.objects.get(username="new-student")
        self.assertTrue(user.check_password(payload["password1"]))
        self.assertNotEqual(user.password, payload["password1"])
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(
            self.client.get("/api/auth/session/").json()["user"]["username"],
            "new-student",
        )
        duplicate = self.client.post(
            "/api/auth/register/", payload, format="json", HTTP_X_CSRFTOKEN=self.token()
        )
        self.assertEqual(duplicate.status_code, 400)

    def test_registration_rejects_weak_or_mismatched_password(self):
        payload = dict(
            username="new-student",
            full_name="Новый студент",
            email="new@example.test",
            password1="123",
            password2="123",
        )
        response = self.client.post(
            "/api/auth/register/", payload, format="json", HTTP_X_CSRFTOKEN=self.token()
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="new-student").exists())

    def test_login_profile_persistence_and_logout(self):
        login_response = self.login_as()
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(
            int(self.client.cookies["sessionid"]["max-age"]), 90 * 24 * 60 * 60
        )
        self.assertEqual(self.client.get("/api/lessons/").status_code, 200)
        with patch(
            "schedule.accounts.fetch_cached",
            return_value={"data": [{"id": 2827, "name": "ИБ-312"}]},
        ):
            response = self.client.patch(
                "/api/auth/profile/",
                {
                    "full_name": "Анна Студентова",
                    "study_form": "full-time",
                    "university_group": "ИБ-312",
                    "is_admin": True,
                },
                format="json",
                HTTP_X_CSRFTOKEN=self.token(),
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_admin"])
        other_client = APIClient(enforce_csrf_checks=True)
        other_client.cookies["sessionid"] = self.client.cookies["sessionid"].value
        session = other_client.get("/api/auth/session/").json()
        self.assertEqual(session["user"]["university_group"], "ИБ-312")
        self.assertEqual(session["user"]["study_form"], "full-time")
        self.assertEqual(session["user"]["full_name"], "Анна Студентова")
        self.assertEqual(
            self.client.post(
                "/api/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=self.token()
            ).status_code,
            200,
        )
        self.assertIsNone(self.client.get("/api/auth/session/").json()["user"])
        self.assertEqual(other_client.get("/api/lessons/").status_code, 403)

    def test_csrf_required_for_login_registration_logout_and_profile(self):
        self.assertEqual(
            self.client.post(
                "/api/auth/login/",
                {"username": "student", "password": "Test-pass-9182!"},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post("/api/auth/register/", {}, format="json").status_code, 403
        )
        self.login_as()
        self.assertEqual(
            self.client.patch(
                "/api/auth/profile/", {"full_name": "Имя"}, format="json"
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post("/api/auth/logout/", {}, format="json").status_code, 403
        )

    def test_wrong_password_and_closed_browser_session(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "student", "password": "wrong"},
            format="json",
            HTTP_X_CSRFTOKEN=self.token(),
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            "/api/auth/login/",
            {"username": "student", "password": "Test-pass-9182!", "remember": False},
            format="json",
            HTTP_X_CSRFTOKEN=self.token(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.cookies["sessionid"]["max-age"])

    def test_student_cannot_create_edit_delete_lessons(self):
        self.login_as()
        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        count = Lesson.objects.count()
        for method, url, payload in [
            ("post", "/api/lessons/", {}),
            ("patch", f"/api/lessons/{lesson.id}/", {"subject": lesson.subject_id}),
            ("delete", f"/api/lessons/{lesson.id}/", {}),
        ]:
            response = getattr(self.client, method)(
                url, payload, format="json", HTTP_X_CSRFTOKEN=self.token()
            )
            self.assertEqual(response.status_code, 403)
        self.assertEqual(Lesson.objects.count(), count)

    def test_admin_can_create_partial_edit_and_delete_with_csrf(self):
        self.login_as("administrator")
        lesson = Lesson.objects.filter(
            group__name="ИСТ-311", day_of_week=1, week_type="odd"
        ).first()
        payload = dict(
            group=lesson.group_id,
            teacher=lesson.teacher_id,
            subject=lesson.subject_id,
            classroom=Classroom.objects.get(
                building__name="Факультет менеджмента и предпринимательства",
                number="305",
            ).pk,
            day_of_week=2,
            week_type="odd",
            start_time="13:00",
            end_time="14:30",
        )
        self.assertEqual(
            self.client.post("/api/lessons/", payload, format="json").status_code, 403
        )
        response = self.client.post(
            "/api/lessons/", payload, format="json", HTTP_X_CSRFTOKEN=self.token()
        )
        self.assertEqual(response.status_code, 201, response.data)
        url = f"/api/lessons/{response.data['id']}/"
        self.assertEqual(
            self.client.patch(
                url, {"end_time": "12:00"}, format="json", HTTP_X_CSRFTOKEN=self.token()
            ).status_code,
            400,
        )
        response = self.client.patch(
            url, {"end_time": "15:00"}, format="json", HTTP_X_CSRFTOKEN=self.token()
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["end_time"], "15:00:00")
        self.assertEqual(
            self.client.delete(
                url, {}, format="json", HTTP_X_CSRFTOKEN=self.token()
            ).status_code,
            204,
        )


class ExportTests(APITransactionTestCase):
    def test_export_permissions_and_contents(self):
        import csv
        from io import BytesIO, StringIO
        from zipfile import ZipFile
        from .exports import csv_bytes

        call_command("seed_schedule", verbosity=0)
        self.assertEqual(self.client.get("/api/export/").status_code, 403)
        user = User.objects.create_user(username="export-student")
        self.client.force_authenticate(user)
        self.assertEqual(self.client.get("/api/export/").status_code, 403)
        user.is_staff = True
        user.save()
        response = self.client.get("/api/export/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        with ZipFile(BytesIO(response.content)) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    "groups.csv",
                    "teachers.csv",
                    "subjects.csv",
                    "campuses.csv",
                    "classrooms.csv",
                    "schedule.csv",
                },
            )
            rows = list(
                csv.reader(
                    StringIO(archive.read("schedule.csv").decode("utf-8-sig")),
                    delimiter=";",
                )
            )
            self.assertEqual(len(rows), Lesson.objects.count() + 1)
            self.assertIn("Преподаватель", rows[0])
            self.assertTrue(archive.read("groups.csv").startswith(b"\xef\xbb\xbf"))
        self.assertIn("'=SUM(1)", csv_bytes(["Имя"], [["=SUM(1)"]]).decode("utf-8-sig"))
