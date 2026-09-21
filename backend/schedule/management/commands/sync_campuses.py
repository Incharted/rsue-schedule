from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from schedule.models import Building, Lesson, Classroom


class Command(BaseCommand):
    help = "Обновить учебные площадки РГЭУ в Ростове по rsue.ru/sveden/common/."

    @transaction.atomic
    def handle(self, *args, **options):
        # Переименовать существующие площадки, сохранив ID и связи расписания.
        names = {
            "Корпус №2": "Факультет менеджмента и предпринимательства",
            "Корпус №3": "Юридический факультет",
            "Корпус №4": "Факультет лингвистики и журналистики",
        }
        for old, new in names.items():
            if not Building.objects.filter(name=new).exists():
                Building.objects.filter(name=old).update(name=new)
        sites = [
            ("Главный корпус", "Ростов-на-Дону, ул. Большая Садовая, 69/47"),
            (
                "Факультет менеджмента и предпринимательства",
                "Ростов-на-Дону, пер. Островского, 62",
            ),
            ("Юридический факультет", "Ростов-на-Дону, ул. Максима Горького, 166"),
            (
                "Факультет лингвистики и журналистики",
                "Ростов-на-Дону, ул. Тургеневская, 49",
            ),
            (
                "Финансово-экономический колледж",
                "Ростов-на-Дону, пер. Доломановский, 53",
            ),
        ]
        for name, address in sites:
            Building.objects.update_or_create(name=name, defaults={"address": address})
        room = Classroom.objects.filter(
            building__name="Факультет менеджмента и предпринимательства", number="305"
        ).first()
        if room:
            Lesson.objects.filter(
                group__name="ИСТ-311",
                teacher__full_name="Кузнецова М.С.",
                subject__name="Высшая математика",
                classroom__building__name="Главный корпус",
                classroom__number="201",
                day_of_week=2,
                week_type="odd",
                start_time=time(10, 40),
                end_time=time(12, 10),
            ).update(classroom=room)
        self.stdout.write(self.style.SUCCESS("Учебные площадки обновлены: 5."))
