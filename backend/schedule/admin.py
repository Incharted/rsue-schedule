from django.contrib import admin

from .models import Building, Classroom, Group, Lesson, Subject, Teacher
from .models import UserProfile

admin.site.register([Group, Teacher, Subject, Building])
admin.site.register(UserProfile)
admin.site.site_header = "РГЭУ (РИНХ) — управление расписанием"
admin.site.site_title = "Администрирование расписания"
admin.site.index_title = "Управление университетским порталом"


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ["number", "building"]
    list_filter = ["building"]
    list_select_related = ["building"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "group",
        "subject",
        "teacher",
        "classroom",
        "day_of_week",
        "week_type",
        "start_time",
        "end_time",
    ]
    list_filter = ["group", "day_of_week", "week_type"]
    list_select_related = ["group", "subject", "teacher", "classroom__building"]
