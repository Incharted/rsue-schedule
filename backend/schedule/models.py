from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


class Group(models.Model):
    class Meta:
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"

    name = models.CharField("Название", max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class StudyForm(models.TextChoices):
        FULL_TIME = "full-time", "Очная"
        PART_TIME = "part-time", "Заочная"
        MIXED = "mixed", "Очно-заочная"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="schedule_profile",
    )
    group = models.ForeignKey(
        Group,
        verbose_name="Учебная группа",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    university_group = models.CharField(
        "Группа университета", max_length=150, blank=True
    )
    study_form = models.CharField(
        "Форма обучения", max_length=20, choices=StudyForm.choices, blank=True
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.user.username


class Teacher(models.Model):
    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"

    full_name = models.CharField("ФИО", max_length=200)

    def __str__(self):
        return self.full_name


class Subject(models.Model):
    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"

    name = models.CharField("Название", max_length=200, unique=True)

    def __str__(self):
        return self.name


class Building(models.Model):
    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпуса"

    name = models.CharField("Название", max_length=100, unique=True)
    address = models.CharField("Адрес", max_length=255, blank=True)

    def __str__(self):
        return self.name


class Classroom(models.Model):
    number = models.CharField("Номер", max_length=20)
    building = models.ForeignKey(
        Building,
        verbose_name="Корпус",
        on_delete=models.PROTECT,
        related_name="classrooms",
    )

    class Meta:
        verbose_name = "Аудитория"
        verbose_name_plural = "Аудитории"
        constraints = [
            models.UniqueConstraint(
                fields=["building", "number"], name="unique_classroom_in_building"
            ),
        ]

    def __str__(self):
        return f"{self.building}, {self.number}"


class Lesson(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 1, "Понедельник"
        TUESDAY = 2, "Вторник"
        WEDNESDAY = 3, "Среда"
        THURSDAY = 4, "Четверг"
        FRIDAY = 5, "Пятница"
        SATURDAY = 6, "Суббота"
        SUNDAY = 7, "Воскресенье"

    class WeekType(models.TextChoices):
        ODD = "odd", "Нечётная"
        EVEN = "even", "Чётная"

    group = models.ForeignKey(
        Group,
        verbose_name="Учебная группа",
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    teacher = models.ForeignKey(
        Teacher,
        verbose_name="Преподаватель",
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    subject = models.ForeignKey(
        Subject,
        verbose_name="Дисциплина",
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    classroom = models.ForeignKey(
        Classroom,
        verbose_name="Аудитория",
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    day_of_week = models.PositiveSmallIntegerField("День недели", choices=Day.choices)
    week_type = models.CharField("Тип недели", max_length=4, choices=WeekType.choices)
    start_time = models.TimeField("Начало")
    end_time = models.TimeField("Окончание")

    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"
        ordering = ["day_of_week", "start_time", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="lesson_end_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(day_of_week__range=(1, 7)), name="lesson_valid_day"
            ),
            models.CheckConstraint(
                condition=models.Q(week_type__in=["odd", "even"]),
                name="lesson_valid_week",
            ),
        ]

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "Окончание должно быть позже начала."})
        if self.group_id and self.classroom_id and self.day_of_week and self.week_type:
            conflict = (
                Lesson.objects.filter(
                    group_id=self.group_id,
                    day_of_week=self.day_of_week,
                    week_type=self.week_type,
                )
                .exclude(pk=self.pk)
                .exclude(classroom__building_id=self.classroom.building_id)
                .select_related("classroom__building")
                .first()
            )
            if conflict:
                raise ValidationError(
                    {
                        "classroom": f"В этот день {self.get_week_type_display().lower()} недели группа уже учится в корпусе «{conflict.classroom.building.name}». Выберите аудиторию в том же корпусе."
                    }
                )

    def __str__(self):
        return f"{self.group}: {self.subject}, {self.get_day_of_week_display()} {self.start_time}"
