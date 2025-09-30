# Questions and Requests for the Repository Owner

1. **GPU TLS certificates**
   Где будут храниться CA/клиентские сертификаты и приватный ключ для mTLS между бэкендом и GPU-сервисами? Нужны точные пути или процедура получения файлов.
   Частичный ответ и текущие допущения собраны в разделе «GPU TLS Certificate Distribution» документа [`docs/researches/2025-09-29-v1-g1-5-asr-manual-test.md`](docs/researches/2025-09-29-v1-g1-5-asr-manual-test.md). Ожидаем от владельца конкретные пути и процесс выдачи сертификатов.

2. **Deep research (G1_5 manual ASR verification prerequisites)**
   Для полноценного закрытия задачи G1_5 нам нужно ручное (не юнит) тестирование ASR-сервиса, но сейчас не хватает конкретики:
   - какая компактная модель Whisper (HF ID) гарантированно помещается в CPU-окружение и какими командами её скачивать заранее;
   - где взять короткий аудиофайл с упоминанием «RUMA», чтобы проверить постобработку, и какой текст считать эталонным результатом;
   - какую структуру каталогов использовать для `request.path`, чтобы сервис увидел файл при запуске отдельно от backend-а;
   - какими точными командами поднимать сервис и дергать gRPC (например, через `grpcurl`), включая значения переменных окружения.
   Пожалуйста, через модель **deep research** подготовьте пошаговый план ручной проверки (установка зависимостей, запуск сервиса на CPU, отправка запроса и сверка ответа). В отчёте обязательно добавьте shell-команды в блоках кода для загрузки выбранной модели, причём в каждой команде должна быть прямая ссылка на источник (например, URL HuggingFace snapshot). Нужны также примеры команд для запуска сервиса и вызова `grpcurl`, ожидаемый текст ответа и подсказки по диагностике (какие логи/симптомы считаем ошибкой).
   Ответ: подробный план и команды находятся в файле [`docs/researches/2025-09-29-v1-g1-5-asr-manual-test.md`](docs/researches/2025-09-29-v1-g1-5-asr-manual-test.md) (раздел «ASR Service Manual Testing Plan (G1_5 Verification)»). Дополнительных запросов не требуется.

3. **Deep research (G2_4 live diarization verification)**
   Please run the deep research model to outline a step-by-step plan for enabling reliable live testing of the diarization service, including staging environment requirements, automated test coverage, telemetry checkpoints, and risk mitigation for production rollout.
   Ответ: подробный план опубликован в [`docs/researches/g2_4_research.md`](docs/researches/g2_4_research.md). Дополнительных запросов не требуется.

4. **Артефакты NeMo для диаризации (smoke-тест CPU)**
   После установки зависимостей командой `GPU_CUDA_VARIANT=cpu ./install_deps.sh --gpu` и запуска `./scripts/diarization_cpu_smoke_test.sh` сервис завершается с ошибкой из-за отсутствия файлов `diar_inference.yaml`, `vad_multilingual_marblenet.nemo`, `titanet_large.nemo` и `msdd_telephonic.nemo` в `gpu_services/models/`. Можно ли добавить облегчённый набор весов в репозиторий тестовых данных или предоставить прямые ссылки с командами скачивания, которые не требуют авторизации? Без артефактов smoke-тест не получится автоматизировать.
