# Documentation

Эта папка содержит актуальную документацию по сервису распознавания встреч. Здесь нужно хранить диаграммы и инструкции по использованию. При изменении архитектуры или бизнес‑процессов обновляйте соответствующие файлы.

## Диаграммы
- **database_diagram.md** – диаграмма базы данных (mermaid)
- **process_overview.md** – общая схема работы сервиса (mermaid)
- **filesystem_structure.md** – схема использования файловой системы (mermaid)
- **gpu_security.md** – варианты защиты подключения к GPU-ноде
- **ai-context/speech_stack_research.md** – результаты исследования стеков моделей и требований к GPU-сервисам
- **secure_storage_todo.md** – требования к защищённому хранилищу

## Переменные окружения
Настройки приложения берутся из файла `.env`, расположенного в корне репозитория.
Укажите переменную `DATABASE_URL` для подключения к базе данных.
Параметры подключения к GPU-ноде собраны в классе `GPUSettings` и имеют префикс
`GPU_`: `GRPC_HOST`, `GRPC_PORT`, `GRPC_USE_TLS`, `GRPC_TLS_CA`,
`GRPC_TLS_CERT`, `GRPC_TLS_KEY`. Если `GPU_GRPC_USE_TLS=true`, пути к
сертификатам обязательны.

## GPU services
Для локального запуска мок-версий моделей используйте файл `infra/docker-compose.gpu.yml`.
Он поднимает контейнеры `asr`, `speaker` и `summarizer` с интерфейсом gRPC.
Все исходные аудио сохраняются во временную папку `data/raw/`. Эти файлы нужно
перенести в защищённое хранилище до конца 2025 года.

## PostgreSQL
Для разработки поднимите локальную базу данных командой:

```bash
docker compose -f infra/docker-compose.dev.yml up -d postgres
```

В CI используйте облегчённую конфигурацию:

```bash
docker compose -f infra/docker-compose.ci.yml up -d postgres
```

Обе конфигурации создают базу `voicerec` с пользователем `voicerec` и включённым healthcheck на основе `pg_isready`.

## Компиляция proto-файлов
Для генерации Python-модулей воспользуйтесь пакетом `grpcio-tools`. Запустите команду:

```bash
python -m grpc_tools.protoc -I ./protos --python_out=./backend/app/protos --grpc_python_out=./backend/app/protos ./protos/*.proto
```

При необходимости создайте папку `backend/app/protos`. В ней появятся файлы `*_pb2.py` и `*_pb2_grpc.py`, которые затем можно импортировать в коде.
