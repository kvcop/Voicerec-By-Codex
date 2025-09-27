# Диаграмма базы данных

Обновлённая ER-диаграмма соответствует сущностям, запланированным в Фазе 1.

```mermaid
erDiagram
    USERS ||--o{ MEETINGS : "owns"
    MEETINGS ||--o{ TRANSCRIPTS : "contains"

    USERS {
        uuid id PK
        string email UNIQUE
        string hashed_password
        timestamptz created_at
        timestamptz updated_at
    }

    MEETINGS {
        uuid id PK
        uuid user_id FK
        string filename
        timestamptz created_at
        status_enum status
    }

    TRANSCRIPTS {
        uuid id PK
        uuid meeting_id FK
        string text
        int speaker_id
        timestamptz timestamp
    }
```

**Ключевые ограничения:** `users.email` — уникальный индекс; внешние ключи связывают встречи с пользователями и транскрипты со встречами; `meetings.user_id` и `transcripts.meeting_id` требуют индексов для быстрого доступа; `meetings.status` хранится как enum (например, `scheduled`, `processing`, `ready`, `failed`).
