# FixDesk - Сервис заявок на ремонт в колледже

Backend для системы управления заявками на ремонт. REST API на Django + Django REST Framework.

## Технологии

- Python 3.13
- Django 5.2
- Django REST Framework
- SQLite (для разработки)
- Pillow (обработка изображений)
- django-filter (фильтрация)
- pytest + pytest-django (тесты)
- Token Authentication (DRF)

## Установка (macOS)

### 1. Клонирование и виртуальное окружение

```bash
cd fix_desk_project
python3 -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` при необходимости (для разработки значения по умолчанию подойдут).

### 4. Миграции базы данных

```bash
python manage.py migrate
```

### 5. Загрузка демо-данных

```bash
python manage.py seed_demo
```

### 6. Запуск сервера

```bash
python manage.py runserver
```

Сервер будет доступен на http://127.0.0.1:8000

## Тестовые аккаунты

После выполнения `seed_demo` создаются следующие аккаунты:

| Роль | Username | Password |
|------|----------|----------|
| Administrator | admin | admin123 |
| Dispatcher | dispatcher | dispatcher123 |
| Executor 1 | executor1 | executor1123 |
| Executor 2 | executor2 | executor2123 |
| Executor 3 | executor3 | executor3123 |
| Requester 1 | requester1 | requester1123 |
| Requester 2 | requester2 | requester2123 |
| Requester 3 | requester3 | requester3123 |

## API Эндпоинты

### Аутентификация

- `POST /api/auth/register` - Регистрация (создаёт requester)
- `POST /api/auth/login` - Вход (возвращает токен)
- `POST /api/auth/logout` - Выход
- `GET /api/auth/me` - Профиль пользователя
- `PATCH /api/auth/me` - Обновление профиля

### Заявки

- `POST /api/tickets` - Создать заявку
- `GET /api/tickets` - Список заявок (пагинация, поиск, фильтры)
- `GET /api/tickets/{id}` - Детализация заявки
- `POST /api/tickets/{id}/assign` - Назначить исполнителя (dispatcher/admin)
- `POST /api/tickets/{id}/reject` - Отклонить заявку (dispatcher/admin)
- `POST /api/tickets/{id}/start` - Взять в работу (executor)
- `POST /api/tickets/{id}/resolve` - Решить заявку (executor)
- `POST /api/tickets/{id}/confirm` - Подтвердить решение (author)
- `POST /api/tickets/{id}/reopen` - Вернуть в работу (author)
- `POST /api/tickets/{id}/comments` - Добавить комментарий

### Прочее

- `GET /api/locations` - Список кабинетов (CRUD для admin)
- `GET /api/categories` - Список категорий (CRUD для admin)
- `GET /api/attachments/{id}/` - Скачать файл
- `GET /api/reports/summary` - Отчёт по заявкам (dispatcher/admin)

## Роли и права доступа

- **requester** - создаёт заявки, видит только свои, может подтверждать/возвращать решённые
- **executor** - видит только назначенные заявки, может брать в работу и решать
- **dispatcher** - видит все заявки, назначает исполнителей, отклоняет заявки
- **admin** - все права dispatcher + управление пользователями/категориями/кабинетами

## Статусы заявок и переходы

```
new → assigned → in_progress → resolved → closed
          ↓
        rejected
resolved → in_progress (возврат автором)
```

## Запуск тестов

```bash
pytest
```

## Проверка на чистой базе

```bash
rm -f db.sqlite3
python manage.py migrate
python manage.py seed_demo
pytest
```

## Структура проекта

```
fix_desk_project/
├── core/                   # Основное приложение
│   ├── models.py          # Модели данных
│   ├── serializers.py     # DRF сериализаторы
│   ├── views.py           # API представления
│   ├── permissions.py     # Классы прав доступа
│   ├── services.py        # Бизнес-логика (переходы статусов)
│   ├── signals.py         # Сигналы Django
│   ├── admin.py           # Админка Django
│   └── management/        # Management команды
│       └── commands/
│           └── seed_demo.py
├── tests/                 # Тесты
│   └── test_api.py
├── docs/                  # Документация
│   └── er-diagram.md
├── fixdesk/              # Настройки Django
├── requirements.txt      # Зависимости Python
├── pytest.ini           # Конфигурация pytest
├── .env.example         # Пример переменных окружения
└── .gitignore          # Игнорируемые файлы
```

## Примечания

- Максимум 3 вложения на заявку (изображения до 5 МБ)
- История изменений статусов сохраняется в TicketHistory
- При возвращении решённой заявки в работу `resolved_at` очищается
- Исполнитель не может переназначить себя на другую заявку
- Автор не может редактировать описание после начала работы
