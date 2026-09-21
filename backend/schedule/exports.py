import csv
from io import StringIO, BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from django.db import connection, transaction
from django.http import HttpResponse
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from .models import Building, Classroom, Group, Lesson, Subject, Teacher


def csv_bytes(headers, rows):
    output = StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(headers)
    for row in rows:
        # Excel не должен исполнять значение из БД как формулу.
        writer.writerow(
            [
                (
                    "'" + value
                    if isinstance(value, str)
                    and value.lstrip().startswith(("=", "+", "-", "@"))
                    else value
                )
                for value in row
            ]
        )
    return output.getvalue().encode("utf-8-sig")


class DataExportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        archive = BytesIO()
        with transaction.atomic(), ZipFile(archive, "w", ZIP_DEFLATED) as result:
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            tables = [
                (
                    "groups",
                    ["ID", "Группа"],
                    Group.objects.order_by("id").values_list("id", "name"),
                ),
                (
                    "teachers",
                    ["ID", "Преподаватель"],
                    Teacher.objects.order_by("id").values_list("id", "full_name"),
                ),
                (
                    "subjects",
                    ["ID", "Дисциплина"],
                    Subject.objects.order_by("id").values_list("id", "name"),
                ),
                (
                    "campuses",
                    ["ID", "Название", "Адрес"],
                    Building.objects.order_by("id").values_list(
                        "id", "name", "address"
                    ),
                ),
                (
                    "classrooms",
                    ["ID", "Аудитория", "ID корпуса", "Корпус"],
                    Classroom.objects.order_by("id").values_list(
                        "id", "number", "building_id", "building__name"
                    ),
                ),
            ]
            for name, headers, rows in tables:
                result.writestr(name + ".csv", csv_bytes(headers, rows))
            lessons = Lesson.objects.select_related(
                "group", "teacher", "subject", "classroom__building"
            ).order_by("group__name", "week_type", "day_of_week", "start_time")
            rows = (
                (
                    lesson.pk,
                    lesson.group.name,
                    lesson.teacher.full_name,
                    lesson.subject.name,
                    lesson.classroom.building.name,
                    lesson.classroom.number,
                    lesson.get_day_of_week_display(),
                    lesson.get_week_type_display(),
                    lesson.start_time.strftime("%H:%M"),
                    lesson.end_time.strftime("%H:%M"),
                )
                for lesson in lessons
            )
            result.writestr(
                "schedule.csv",
                csv_bytes(
                    [
                        "ID",
                        "Группа",
                        "Преподаватель",
                        "Дисциплина",
                        "Корпус",
                        "Аудитория",
                        "День",
                        "Неделя",
                        "Начало",
                        "Конец",
                    ],
                    rows,
                ),
            )
        response = HttpResponse(archive.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = (
            'attachment; filename="rgeu-catalog-export.zip"'
        )
        response["Cache-Control"] = "no-store"
        return response
