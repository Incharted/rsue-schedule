from django.urls import path

from .upstream import university_schedule
from . import views
from . import accounts
from .exports import DataExportView

app_name = "schedule"

urlpatterns = [
    path("university/", university_schedule),
    path("export/", DataExportView.as_view(), name="export"),
    path("auth/session/", accounts.session_view),
    path("auth/register/", accounts.register_view),
    path("auth/login/", accounts.login_view),
    path("auth/logout/", accounts.logout_view),
    path("auth/profile/", accounts.ProfileView.as_view()),
    path("groups/", views.GroupListView.as_view(), name="groups"),
    path("teachers/", views.TeacherListView.as_view(), name="teachers"),
    path("subjects/", views.SubjectListView.as_view(), name="subjects"),
    path("buildings/", views.BuildingListView.as_view(), name="buildings"),
    path("classrooms/", views.ClassroomListView.as_view(), name="classrooms"),
    path("lessons/", views.LessonListCreateView.as_view(), name="lessons"),
    path("lessons/<int:pk>/", views.LessonDetailView.as_view(), name="lesson-detail"),
]
