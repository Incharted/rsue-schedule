import json

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile
from .upstream import entry_category, fetch_cached, search_entries


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(label="Имя и фамилия", max_length=150)
    email = forms.EmailField(label="Электронная почта")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "full_name")


def user_data(user):
    if not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.first_name or user.username,
        "email": user.email,
        "is_admin": user.is_staff,
        "university_group": profile.university_group or None,
        "study_form": profile.study_form or None,
    }


def read_json(request):
    try:
        data = json.loads(request.body)
        return data if isinstance(data, dict) else None
    except (ValueError, UnicodeDecodeError):
        return None


def session_response(request):
    return JsonResponse(
        {"user": user_data(request.user), "csrfToken": get_token(request)}
    )


@require_GET
@ensure_csrf_cookie
def session_view(request):
    return session_response(request)


@require_POST
@csrf_protect
def register_view(request):
    data = read_json(request)
    if data is None:
        return JsonResponse({"detail": "Некорректный формат данных."}, status=400)
    form = RegistrationForm(data)
    if not form.is_valid():
        return JsonResponse(
            {"errors": {key: list(value) for key, value in form.errors.items()}},
            status=400,
        )
    with transaction.atomic():
        user = form.save(commit=False)
        user.first_name = form.cleaned_data["full_name"]
        # Регистрация никогда не выдаёт права администратора.
        user.is_staff = False
        user.is_superuser = False
        user.save()
        UserProfile.objects.create(user=user)
    login(request, user)
    request.session.set_expiry(60 * 60 * 24 * 90)
    response = session_response(request)
    response.status_code = 201
    return response


@require_POST
@csrf_protect
def login_view(request):
    data = read_json(request)
    if data is None:
        return JsonResponse({"detail": "Некорректный формат данных."}, status=400)
    username = data.get("username", "")
    password = data.get("password", "")
    if not isinstance(username, str) or not isinstance(password, str):
        return JsonResponse({"detail": "Введите логин и пароль."}, status=400)
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"detail": "Неверный логин или пароль."}, status=400)
    login(request, user)
    request.session.set_expiry(60 * 60 * 24 * 90 if data.get("remember") is True else 0)
    return session_response(request)


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return session_response(request)


def csrf_failure(request, reason=""):
    return JsonResponse(
        {"detail": "Сессия страницы устарела. Обновите страницу и повторите действие."},
        status=403,
    )


class ProfileSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    university_group = serializers.CharField(
        max_length=150, allow_blank=True, required=False
    )
    study_form = serializers.ChoiceField(
        choices=UserProfile.StudyForm.choices, allow_blank=True, required=False
    )

    def validate(self, attrs):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.context["request"].user
        )
        group = attrs.get("university_group", profile.university_group).strip()
        study_form = attrs.get("study_form", profile.study_form)
        if bool(group) != bool(study_form):
            raise serializers.ValidationError(
                {"university_group": "Выберите форму обучения и группу."}
            )
        if group:
            if entry_category(group) != study_form:
                raise serializers.ValidationError(
                    {
                        "university_group": "Группа не относится к выбранной форме обучения."
                    }
                )
            try:
                entries = fetch_cached("search/", search_entries)["data"]
            except (OSError, ValueError, KeyError, TypeError):
                raise serializers.ValidationError(
                    {"university_group": "Справочник университета временно недоступен."}
                )
            if group not in {item["name"] for item in entries}:
                raise serializers.ValidationError(
                    {"university_group": "Такой группы нет в справочнике университета."}
                )
        attrs["university_group"] = group
        attrs["study_form"] = study_form
        return attrs


class ProfileView(APIView):
    def get(self, request):
        return Response(user_data(request.user))

    def patch(self, request):
        serializer = ProfileSerializer(
            data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            user = request.user
            user.first_name = data.get("full_name", user.first_name)
            user.email = data.get("email", user.email)
            user.save(update_fields=["first_name", "email"])
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.university_group = data.get(
                "university_group", profile.university_group
            )
            profile.study_form = data.get("study_form", profile.study_form)
            profile.save(update_fields=["university_group", "study_form"])
        return Response(user_data(request.user))
