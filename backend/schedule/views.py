from rest_framework import generics
from django.db import transaction

from .models import Building, Classroom, Group, Lesson, Subject, Teacher
from .permissions import IsAdminOrReadOnly
from .serializers import (
    BuildingSerializer,
    ClassroomSerializer,
    GroupSerializer,
    LessonFilterSerializer,
    LessonSerializer,
    SubjectSerializer,
    TeacherSerializer,
)


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.order_by("name", "id")
    serializer_class = GroupSerializer


class TeacherListView(generics.ListAPIView):
    queryset = Teacher.objects.order_by("full_name", "id")
    serializer_class = TeacherSerializer


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.order_by("name", "id")
    serializer_class = SubjectSerializer


class BuildingListView(generics.ListAPIView):
    queryset = Building.objects.order_by("name", "id")
    serializer_class = BuildingSerializer


class ClassroomListView(generics.ListAPIView):
    queryset = Classroom.objects.select_related("building").order_by(
        "building__name", "number", "id"
    )
    serializer_class = ClassroomSerializer


class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        with transaction.atomic():
            Group.objects.select_for_update().get(
                pk=serializer.validated_data["group"].pk
            )
            serializer.validate(serializer.validated_data)
            serializer.save()

    def get_queryset(self):
        filters = LessonFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        return Lesson.objects.select_related(
            "group",
            "teacher",
            "subject",
            "classroom__building",
        ).filter(**filters.validated_data)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related(
        "group", "teacher", "subject", "classroom__building"
    )
    serializer_class = LessonSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_update(self, serializer):
        with transaction.atomic():
            group = serializer.validated_data.get("group", serializer.instance.group)
            list(
                Group.objects.select_for_update()
                .filter(pk__in=[group.pk, serializer.instance.group_id])
                .order_by("pk")
            )
            serializer.validate(serializer.validated_data)
            serializer.save()
