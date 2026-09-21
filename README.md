# Расписание РГЭУ (РИНХ)

Веб-приложение для студентов: расписание своей группы, ближайшие занятия, поиск преподавателей и адреса корпусов. Проект выполнен как Full Stack задание на Django, PostgreSQL и Vue.

После регистрации можно выбрать форму обучения и основную группу в профиле. Выбор сохраняется в аккаунте: главная и расписание используют одну группу, в том числе после входа с другого устройства. Просмотр другой группы или преподавателя не меняет настройки профиля.

## Стек

- **Backend:** Python, Django, Django REST Framework.
- **Frontend:** Vue 3, Vue Router, Vuetify, Vite.
- **База данных:** PostgreSQL 17.
- **Авторизация:** сессии Django, CSRF-защита, отдельные права администратора.

## Как устроены данные

Frontend получает данные через REST API Django. Расписание и справочник преподавателей загружаются из API РГЭУ через адаптер `backend/schedule/upstream.py`. Он сохраняет конкретные даты, время и подгруппы. Ответ считается свежим 15 минут; при сбое используется последняя успешная версия, если ей не больше семи дней. Для первого получения данных нужен интернет.

PostgreSQL хранит аккаунты, профили и локальные таблицы групп, преподавателей, дисциплин, корпусов, аудиторий и занятий. Локальный каталог используется для CRUD, SQL-запросов и экспорта. Его начальные занятия — примеры, а не копия действующего расписания РГЭУ. Изменения в Django Admin не меняют внешнее расписание.

Внешний API не сообщает форму обучения отдельным полем, поэтому категория определяется по названию записи. Аудитории отображаются так, как они пришли из источника: корпус по номеру автоматически не назначается.

## Локальный запуск

Нужны Python 3.12+, Node.js 22.12+ и PostgreSQL 17. Ниже — команды для PowerShell. PostgreSQL должен быть запущен, а его утилиты доступны в PATH.

```powershell
git clone https://github.com/Incharted/rsue-schedule.git
cd rsue-schedule
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Создайте базу и укажите пароль своего пользователя PostgreSQL:

```powershell
createdb -h 127.0.0.1 -U postgres university_schedule
$env:POSTGRES_PASSWORD = 'ваш пароль PostgreSQL'
.\.venv\Scripts\python.exe backend/manage.py migrate
.\.venv\Scripts\python.exe backend/manage.py seed_schedule
.\.venv\Scripts\python.exe backend/manage.py createsuperuser
powershell -ExecutionPolicy Bypass -File .\start.ps1 backend
```

В другом окне PowerShell, из корня проекта:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1 frontend
```

Откройте [приложение](http://127.0.0.1:5173/) или [Django Admin](http://127.0.0.1:8000/admin/). Для администрирования используйте аккаунт, созданный командой `createsuperuser`. Обычная регистрация не выдаёт права администратора. Флажок «Запомнить меня» сохраняет сессию на 90 дней, без него сессия действует до закрытия браузера.

После перезапуска компьютера достаточно запустить PostgreSQL, backend и frontend. Переменные среды нужно задавать в окне backend заново, если они не сохранены в настройках системы. Команда `start.ps1 database` поддерживает локальную переносную PostgreSQL, но сама PostgreSQL и её рабочий каталог в Git не входят.

## Настройки

Настройки читаются из переменных среды. `.env.example` содержит образец; автоматической загрузки `.env` нет.

| Переменная | Значение по умолчанию |
| --- | --- |
| `POSTGRES_DB` | `university_schedule` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | пустая строка |
| `POSTGRES_HOST` | `127.0.0.1` |
| `POSTGRES_PORT` | `5432` |
| `DJANGO_DEBUG` | `True` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | `http://127.0.0.1:5173,http://localhost:5173` |

Для размещения на сервере нужны `DJANGO_DEBUG=False`, собственный случайный `DJANGO_SECRET_KEY`, разрешённые домены и HTTPS. При отключении DEBUG включаются защищённые cookie и перенаправление на HTTPS. Команды выше запускают серверы разработки.

## API

| Адрес | Методы | Назначение |
| --- | --- | --- |
| `/api/auth/session/` | GET | Сессия и CSRF-токен |
| `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/` | POST | Регистрация, вход и выход |
| `/api/auth/profile/` | GET, PATCH | Профиль и основная группа |
| `/api/university/` | GET | Справочник РГЭУ |
| `/api/university/?name=ИБ-312` | GET | Расписание по названию группы или преподавателя |
| `/api/groups/`, `/api/teachers/`, `/api/subjects/` | GET | Локальные справочники |
| `/api/buildings/`, `/api/classrooms/` | GET | Корпуса и аудитории |
| `/api/lessons/` | GET, POST | Локальные занятия |
| `/api/lessons/<id>/` | GET, PUT, PATCH, DELETE | Локальное занятие |
| `/api/export/` | GET | Экспорт локального каталога |

Профиль, справочники и расписание требуют входа. Изменение занятий и экспорт доступны администраторам. Для запросов записи нужен заголовок `X-CSRFToken`. Список локальных занятий поддерживает фильтры `group`, `teacher`, `day_of_week` и `week_type`.

## База данных и выгрузка

В меню администратора доступен «Экспорт данных»: ZIP с шестью CSV-файлами в UTF-8 BOM, разделитель — точка с запятой. Аккаунты и сессии в выгрузку не включаются.

`sql/queries.sql` содержит SQL-запросы задания. В `sql/database_dump.sql` находится схема и начальный локальный каталог без пользователей, профилей и сессий. Вместо миграций и заполнения можно восстановить дамп в пустую базу:

```powershell
psql -h 127.0.0.1 -U postgres -d university_schedule -v ON_ERROR_STOP=1 -f sql/database_dump.sql
.\.venv\Scripts\python.exe backend/manage.py createsuperuser
```

Рабочая база `.pgdata` остаётся на локальном компьютере и исключена из Git.

## Проверки

```powershell
.\.venv\Scripts\python.exe backend/manage.py check
.\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe backend/manage.py test schedule.tests schedule.test_upstream
cd frontend
npm run build
```

Тесты проверяют роли, CSRF, сохранение профиля, фильтры, ограничения данных, экспорт и кеширование внешнего расписания. Для тестов пользователь PostgreSQL должен иметь право создавать тестовую базу. Сборка frontend находится в `frontend/dist`.

## Структура

```text
backend/config/       настройки и маршруты Django
backend/schedule/     модели, REST API, интеграция и тесты
frontend/src/views/   страницы приложения
frontend/src/api.js   HTTP-клиент и состояние сессии
sql/                  схема, начальные данные и запросы
start.ps1             запуск компонентов в Windows
```
