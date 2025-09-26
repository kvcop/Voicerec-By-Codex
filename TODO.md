# TODO

Отмечайте прогресс в колонке **DONE**: пока задача не выполнена, ставьте «✗», после завершения замените на «✓».

| ID | DONE | Задача | Область | Приоритет | Зависимости |
| --- | --- | --- | --- | --- | --- |
| DX1 | ✓ | Добавить `data/raw/` (и подобные артефакты) в `.gitignore`, исключить уже попавшие файлы из репо | Repo/DevEx | P0 | — |
| B1 | ✗ | Базовая ORM-инфраструктура: `DeclarativeBase`, `metadata`, точка импорта моделей | Backend/DB | P0 | — |
| B2 | ✗ | Модели **User, Meeting, Transcript** с связями/индексами | Backend/DB | P0 | B1 |
| B3 | ✗ | Репозитории (CRUD) в `app/db/repositories/` (или единый слой данных) | Backend/DB | P0 | B1–B2 |
| T1 | ✗ | Async тестовая БД (SQLite/aiosqlite), фикстуры, создание/очистка схемы, FastAPI overrides | Tests/Infra | P0 | B1 |
| A2 | ✗ | `/upload`: асинхронная потоковая запись чанками + проверка MIME; негативные/large-file тесты | Backend/API | P0 | — |
| S1 | ✗ | Вынести `TranscriptService` в сервисный слой и внедрять через DI (FastAPI Depends); принимать `AsyncSession` и (в будущем) gRPC-клиентов | Backend/Services | P0 | B1–B3, T1 |
| A1 | ✗ | Выровнять маршруты с докой: префикс `/api/meeting` для upload/stream + подключение роутера | Backend/API | P1 | — |
| A3 | ✗ | Конфигурируемый путь хранения сырого аудио (через настройки/зависимости), поддержать переопределение в тестах | Backend/Config | P1 | A2 |
| L1 | ✗ | Структурированное логирование + HTTP-middleware в `app.main` (`loguru` предпочтительно); smoke-тест (caplog) и краткая дока | Backend/Core | P1 | — |
| F1 | ✗ | Frontend SSE-компонент: `EventSource` к `/api/meeting/stream/{meeting_id}`, состояние/локализация, vitest | Frontend/SSE | P1 | A1 |
| D1 | ✗ | Обновить доку (process_overview/README/CONTEXT): логирование, маршруты, хранилище аудио, модели/репозитории, тест-инфра | Docs | P1 | B1–B3, A1–A3, L1, T1 |
| A4 | ✗ | Починить дефолтный бэкенд-стриминг SSE: `TranscriptService.stream_transcript` должен возвращать `AsyncIterable`; корректный `_event_generator`, heartbeat/timeout | Backend/API/SSE | P1 | S1 |
| D2 | ✗ | Синхронизировать пути в плане с деревом проекта: `backend/app/db/...` вместо `backend/app/database/...`; убрать ссылки на несуществующие тесты/каталоги | Docs/Plan | P1 | — |
| I1 | ✗ | Добавить PostgreSQL в docker-compose (dev/CI), базовые параметры и healthchecks | Infra | P1 | — |
| F2 | ✗ | Почистить фронтенд-зависимости, обновить lock/README, добавить vitest smoke-snapshot | Frontend/Build | P2 | — |
| T2 | ✗ | Убрать `sys.path.append` из тестов: оформить backend как installable package или корректно настроить PYTHONPATH/uv; обновить инструкции | Tests/Infra | P2 | — |
| F3 | ✓ | Локализовать кнопку “Close” в диалоге (i18n словари, переключение языка) | Frontend/i18n | P2 | — |
| F4 | ✗ | Заменить `next-intl` на Vite-дружелюбную i18n-библиотеку (напр., `react-intl`/`use-intl`/`lingui`) | Frontend/i18n | P2 | F2 |

## Предлагаемые параллельные треки

- DX1 — инфраструктурная задача по `.gitignore`, не имеет зависимостей.
- A2 — улучшение загрузки файлов и тестов, можно выполнять независимо от остальных блоков.
- L1 — настройка логирования и middleware, не зависит от других изменений.
- I1 — расширение docker-compose, можно делать параллельно с остальными задачами.
