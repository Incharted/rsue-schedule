from rest_framework import serializers
from django.core.exceptions import ValidationError

from .models import Building, Classroom, Group, Lesson, Subject, Teacher


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ["id", "full_name"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ["id", "name", "address"]


class ClassroomSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source="building.name", read_only=True)

    class Meta:
        model = Classroom
        fields = ["id", "number", "building", "building_name"]


class LessonSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    classroom_number = serializers.CharField(source="classroom.number", read_only=True)
    building_name = serializers.CharField(
        source="classroom.building.name", read_only=True
    )

    class Meta:
        model = Lesson
        fields = [
            "id",
            "group",
            "group_name",
            "teacher",
            "teacher_name",
            "subject",
            "subject_name",
            "classroom",
            "classroom_number",
            "building_name",
            "day_of_week",
            "week_type",
            "start_time",
            "end_time",
        ]

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "Окончание должно быть позже начала."}
            )
        candidate = Lesson()
        if self.instance:
            candidate.pk = self.instance.pk
            for field in Lesson._meta.concrete_fields:
                if not field.primary_key:
                    setattr(
                        candidate, field.attname, getattr(self.instance, field.attname)
                    )
        for name, value in attrs.items():
            setattr(candidate, name, value)
        try:
            candidate.clean()
        except ValidationError as error:
            raise serializers.ValidationError(error.message_dict)
        return attrs


class LessonFilterSerializer(serializers.Serializer):
    group = serializers.IntegerField(min_value=1, required=False)
    teacher = serializers.IntegerField(min_value=1, required=False)
    day_of_week = serializers.ChoiceField(choices=Lesson.Day.choices, required=False)
    week_type = serializers.ChoiceField(choices=Lesson.WeekType.choices, required=False)
