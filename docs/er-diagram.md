# ER-диаграмма FixDesk

```mermaid
erDiagram
    User ||--o{ Ticket : "author"
    User ||--o{ Ticket : "assignee"
    User ||--o{ Comment : "author"
    User ||--o{ TicketHistory : "actor"

    Location ||--o{ Ticket : ""
    Category ||--o{ Ticket : ""

    Ticket ||--o{ Attachment : ""
    Ticket ||--o{ Comment : ""
    Ticket ||--o{ TicketHistory : ""

    User {
        BigInteger id PK
        String username UK
        String email
        String role
        String password
        String first_name
        String last_name
        Boolean is_staff
        Boolean is_active
    }

    Location {
        BigInteger id PK
        String building
        String room
    }

    Category {
        BigInteger id PK
        String name UK
    }

    Ticket {
        BigInteger id PK
        BigInteger author FK
        BigInteger assignee FK
        BigInteger location FK
        BigInteger category FK
        String title
        Text description
        String priority
        String status
        DateTime created_at
        DateTime resolved_at
    }

    Attachment {
        BigInteger id PK
        BigInteger ticket FK
        ImageFile file
    }

    Comment {
        BigInteger id PK
        BigInteger ticket FK
        BigInteger author FK
        Text text
        DateTime created_at
    }

    TicketHistory {
        BigInteger id PK
        BigInteger ticket FK
        BigInteger actor FK
        String old_status
        String new_status
        Text note
        DateTime created_at
    }
```

## Обоснование отклонений от предложенной модели

Модель полностью соответствует требованиям ТЗ. Отклонений нет:

1. **User** - кастомная модель с полем `role`, наследуется от AbstractUser
2. **Location** - уникальность на (building, room) реализована через unique_together
3. **Category** - уникальность на name
4. **Ticket** - все поля согласно ТЗ, индексы на FK и полях фильтров
5. **Attachment** - связь с Ticket, валидация на максимум 3 файла через signal
6. **Comment** - связь с Ticket и User
7. **TicketHistory** - связь с Ticket и User, on_delete=PROTECT для защиты истории

Все индексы добавлены на FK, поля фильтров и сортировки как указано в ТЗ.
