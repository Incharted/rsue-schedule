from datetime import time

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

from schedule.models import Building, Classroom, Group, Lesson, Subject, Teacher


class Command(BaseCommand):
    help = (
        "Добавить начальные справочники и расписание без удаления существующих записей."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("sync_campuses", verbosity=0)
        group, _ = Group.objects.get_or_create(name="ИСТ-311")
        other_group, _ = Group.objects.get_or_create(name="ИСТ-312")
        teacher, _ = Teacher.objects.get_or_create(full_name="Долженко А.И.")
        other_teacher, _ = Teacher.objects.get_or_create(full_name="Иванова Е.В.")
        subject, _ = Subject.objects.get_or_create(name="Базы данных")
        other_subject, _ = Subject.objects.get_or_create(name="Программирование")
        building, _ = Building.objects.get_or_create(name="Главный корпус")
        classroom, _ = Classroom.objects.get_or_create(building=building, number="212")
        other_classroom, _ = Classroom.objects.get_or_create(
            building=building, number="214"
        )
        rows = [
            (group, teacher, subject, classroom, 1, "odd", time(9), time(10, 30)),
            (
                group,
                other_teacher,
                other_subject,
                other_classroom,
                1,
                "odd",
                time(10, 40),
                time(12, 10),
            ),
            (group, teacher, subject, classroom, 1, "even", time(9), time(10, 30)),
            (other_group, teacher, subject, classroom, 3, "odd", time(9), time(10, 30)),
            (
                group,
                other_teacher,
                other_subject,
                classroom,
                3,
                "even",
                time(10, 40),
                time(12, 10),
            ),
        ]
        second_building, _ = Building.objects.get_or_create(
            name="Факультет менеджмента и предпринимательства"
        )
        new_room, _ = Classroom.objects.get_or_create(
            building=second_building, number="305"
        )
        math_room, _ = Classroom.objects.get_or_create(building=building, number="201")
        web_teacher, _ = Teacher.objects.get_or_create(full_name="Смирнов Д.А.")
        math_teacher, _ = Teacher.objects.get_or_create(full_name="Кузнецова М.С.")
        web_subject, _ = Subject.objects.get_or_create(name="Веб-разработка")
        math_subject, _ = Subject.objects.get_or_create(name="Высшая математика")
        rows.extend(
            [
                (
                    group,
                    web_teacher,
                    web_subject,
                    new_room,
                    2,
                    "odd",
                    time(9),
                    time(10, 30),
                ),
                (
                    group,
                    math_teacher,
                    math_subject,
                    new_room,
                    2,
                    "odd",
                    time(10, 40),
                    time(12, 10),
                ),
                (
                    group,
                    web_teacher,
                    web_subject,
                    new_room,
                    4,
                    "odd",
                    time(9),
                    time(10, 30),
                ),
                (
                    group,
                    math_teacher,
                    math_subject,
                    math_room,
                    5,
                    "odd",
                    time(10, 40),
                    time(12, 10),
                ),
                (
                    group,
                    other_teacher,
                    other_subject,
                    other_classroom,
                    6,
                    "odd",
                    time(9),
                    time(10, 30),
                ),
                (
                    group,
                    math_teacher,
                    math_subject,
                    math_room,
                    2,
                    "even",
                    time(9),
                    time(10, 30),
                ),
                (
                    group,
                    web_teacher,
                    web_subject,
                    new_room,
                    4,
                    "even",
                    time(10, 40),
                    time(12, 10),
                ),
                (group, teacher, subject, classroom, 5, "even", time(9), time(10, 30)),
                (
                    other_group,
                    math_teacher,
                    math_subject,
                    math_room,
                    1,
                    "odd",
                    time(9),
                    time(10, 30),
                ),
                (
                    other_group,
                    web_teacher,
                    web_subject,
                    new_room,
                    2,
                    "odd",
                    time(13),
                    time(14, 30),
                ),
                (
                    other_group,
                    other_teacher,
                    other_subject,
                    other_classroom,
                    4,
                    "odd",
                    time(10, 40),
                    time(12, 10),
                ),
                (
                    other_group,
                    teacher,
                    subject,
                    classroom,
                    1,
                    "even",
                    time(10, 40),
                    time(12, 10),
                ),
                (
                    other_group,
                    math_teacher,
                    math_subject,
                    math_room,
                    3,
                    "even",
                    time(9),
                    time(10, 30),
                ),
            ]
        )
        created_count = 0
        for group, teacher, subject, classroom, day, week, start, end in rows:
            _, created = Lesson.objects.get_or_create(
                group=group,
                teacher=teacher,
                subject=subject,
                classroom=classroom,
                day_of_week=day,
                week_type=week,
                start_time=start,
                end_time=end,
            )
            created_count += created
        self.stdout.write(self.style.SUCCESS(f"Добавлено занятий: {created_count}."))
        call_command("seed_catalog", verbosity=0)
