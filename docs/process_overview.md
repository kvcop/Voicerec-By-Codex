# Общая схема работы сервиса

Диаграмма отражает текущую реализацию бэкенда: поток загрузки аудио, хранение, вызов
ML‑пайплайна и возврат результатов через SSE.

```mermaid
flowchart TD
    subgraph client[Клиент]
        ui[Веб-интерфейс]
    end

    subgraph api[FastAPI приложение]
        middleware[HTTP middleware логирования]
        upload[POST /api/meeting/upload]
        stream[GET /api/meeting/{meeting_id}/stream]
    end

    subgraph storage[Файловое хранилище]
        raw[data/raw/<meeting_id>.wav]
    end

    subgraph services[Service layer]
        transcript[TranscriptService]
        meeting_proc[MeetingProcessingService]
    end

    subgraph gpu[Mock gRPC клиенты]
        diarize[Diarize]
        transcribe[Transcribe]
        summarize[Summarize]
    end

    subgraph db[SQLAlchemy слой]
        models[Модели User/Meeting/Transcript]
        repos[Репозитории CRUD]
    end

    ui --> middleware --> upload
    upload --> raw
    raw --> transcript
    transcript --> meeting_proc
    meeting_proc --> diarize
    meeting_proc --> transcribe
    meeting_proc --> summarize
    meeting_proc --> transcript
    transcript --> repos
    repos --> models
    transcript --> stream
    stream --> ui
```
