from datetime import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from schedule.models import Building, Classroom, Group, Lesson, Subject, Teacher


class Command(BaseCommand):
    help = "Дополнить справочники и расписание учебными примерами без удаления данных."

    @transaction.atomic
    def handle(self, *args, **options):
        names = [
            "Петров А.С.",
            "Соколова Н.В.",
            "Волков И.П.",
            "Морозова О.А.",
            "Новиков С.В.",
            "Фёдорова Е.А.",
            "Орлов М.Д.",
            "Лебедева Т.С.",
            "Васильев Р.Н.",
            "Зайцева Л.П.",
            "Белов К.А.",
            "Павлова Ю.В.",
        ]
        teachers = [Teacher.objects.get_or_create(full_name=name)[0] for name in names]
        subjects = [
            Subject.objects.get_or_create(name=name)[0]
            for name in [
                "Алгоритмы и структуры данных",
                "Операционные системы",
                "Компьютерные сети",
                "Информационная безопасность",
                "Теория вероятностей",
                "Статистика",
                "Микроэкономика",
                "Макроэкономика",
                "Бухгалтерский учёт",
                "Финансовый менеджмент",
                "Гражданское право",
                "Теория государства и права",
                "Иностранный язык",
                "Деловые коммуникации",
            ]
        ]
        buildings = list(Building.objects.order_by("id"))
        if len(buildings) != 5:
            raise CommandError("Сначала выполните sync_campuses.")
        rooms = {
            building.pk: [
                Classroom.objects.get_or_create(building=building, number=str(number))[
                    0
                ]
                for number in (401, 402, 403)
            ]
            for building in buildings
        }
        group_names = [
            "ИСТ-211",
            "ИСТ-212",
            "ИБ-211",
            "ИБ-311",
            "ЭК-211",
            "ЭК-311",
            "МЕН-211",
            "МЕН-311",
            "ЮР-211",
            "ЛИН-211",
        ]
        slots = [
            (time(8, 30), time(10)),
            (time(10, 10), time(11, 40)),
            (time(11, 50), time(13, 20)),
            (time(13, 50), time(15, 20)),
            (time(15, 30), time(17)),
            (time(17, 10), time(18, 40)),
            (time(18, 45), time(20, 15)),
            (time(20, 20), time(21, 50)),
        ]
        created = 0
        for index, name in enumerate(group_names):
            group = Group.objects.get_or_create(name=name)[0]
            for week_index, week in enumerate(("odd", "even")):
                for day in range(1, 6):
                    existing = group.lessons.filter(
                        day_of_week=day, week_type=week
                    ).first()
                    building = (
                        existing.classroom.building
                        if existing
                        else buildings[(index + day + week_index) % 5]
                    )
                    for pair in range(2):
                        subject = subjects[
                            (index * 3 + day * 2 + pair + week_index) % len(subjects)
                        ]
                        teacher = teachers[
                            (index + day * 2 + pair + week_index) % len(teachers)
                        ]
                        # Повторное заполнение не дублирует и не перезаписывает уже сохранённые пары.
                        if group.lessons.filter(
                            day_of_week=day,
                            week_type=week,
                            subject=subject,
                            teacher=teacher,
                        ).exists():
                            continue
                        scheduled = False
                        for start, end in slots:
                            busy = Lesson.objects.filter(
                                day_of_week=day,
                                week_type=week,
                                start_time__lt=end,
                                end_time__gt=start,
                            )
                            if (
                                busy.filter(group=group).exists()
                                or busy.filter(teacher=teacher).exists()
                            ):
                                continue
                            for room in rooms[building.pk]:
                                if busy.filter(classroom=room).exists():
                                    continue
                                lesson = Lesson(
                                    group=group,
                                    teacher=teacher,
                                    subject=subject,
                                    classroom=room,
                                    day_of_week=day,
                                    week_type=week,
                                    start_time=start,
                                    end_time=end,
                                )
                                lesson.full_clean()
                                lesson.save()
                                created += 1
                                scheduled = True
                                break
                            if scheduled:
                                break
                        if not scheduled:
                            raise CommandError(
                                f"Не найден свободный слот для {name}, день {day}, {week}."
                            )
        self.stdout.write(self.style.SUCCESS(f"Добавлено занятий: {created}."))
