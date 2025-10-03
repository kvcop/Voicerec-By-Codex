# Ручное тестирование диаризации

Этот документ описывает последовательность действий для локальной проверки gRPC-сервиса диаризации. Инструкции рассчитаны на владельца репозитория и предполагают полный доступ к GPU-машине. Для удобства шаги разделены на подготовку окружения, загрузку моделей, запуск сервиса и smoke-тест. В конце приведены наблюдения о том, что удалось повторить на CPU и какие этапы требуют GPU.

## 1. Подготовка окружения

1. Убедитесь, что система соответствует требованиям NVIDIA NeMo:
   - установлен драйвер NVIDIA с поддержкой CUDA 11.8+;
   - доступен `nvidia-smi` и видна хотя бы одна видеокарта;
   - установлены системные зависимости для `ffmpeg`, `sox`, `libsndfile1` (они нужны NeMo для работы с аудио).
2. Клонируйте репозиторий и перейдите в корневую директорию:
   ```bash
   git clone git@github.com:kvcop/Voicerec-By-Codex.git
   cd Voicerec-By-Codex
   ```
3. Установите Python-зависимости для GPU-части. Скрипт разворачивает виртуальное окружение `gpu_services/.venv`.
   ```bash
   ./install_deps.sh --gpu
   ```
   > Если окружение разворачивается на CPU-машине (для проверки вспомогательных шагов), используйте `GPU_CUDA_VARIANT=cpu ./install_deps.sh --gpu`. Обратите внимание, что без CUDA inference сильно замедлится и не покрывает все сценарии.

## 2. Загрузка артефактов NeMo

Набор артефактов описан в `docs/researches/2025-10-01-v2-g2-4-diarization-testing.md`. Ниже приведены прямые команды загрузки. Файлы нужно положить в `gpu_services/models/`.

```bash
mkdir -p gpu_services/models
cd gpu_services/models

# VAD (Frame_VAD_Multilingual_MarbleNet_v2.0)
wget -O vad_multilingual_marblenet.nemo \
  "https://huggingface.co/nvidia/Frame_VAD_Multilingual_MarbleNet_v2.0/resolve/main/frame_vad_multilingual_marblenet_v2.0.nemo"

# Speaker encoder (TitaNet-Large)
wget -O titanet_large.nemo \
  "https://huggingface.co/nvidia/speakerverification_en_titanet_large/resolve/main/speakerverification_en_titanet_large.nemo"

# Опционально: MSDD (через публичный NGC API)
wget -O msdd_telephonic.nemo \
  "https://api.ngc.nvidia.com/v2/models/nvidia/nemo/diar_msdd_telephonic/versions/1.0.1/files/diar_msdd_telephonic.nemo"
```

Проверьте контрольные суммы, чтобы исключить повреждение скаченных файлов:

```bash
cat > checksums.sha256 <<'SHA'
84bda37e925ac6fd740c2ced55642cb79f94f81348e1fa0db992ca50d4b09706  vad_multilingual_marblenet.nemo
e838520693f269e7984f55bc8eb3c2d60ccf246bf4b896d4be9bcabe3e4b0fe3  titanet_large.nemo
SHA

sha256sum -c checksums.sha256
```

Для MSDD модель из NGC проверьте хеш вручную, так как NVIDIA не публикует его рядом с артефактом. Если загрузка через `wget` недоступна, используйте NGC CLI (`ngc registry model download ...`).

Вернитесь в корень репозитория после скачивания:

```bash
cd ../../
```

## 3. Конфигурация `diar_inference.yaml`

NeMo использует YAML-конфиг, чтобы собрать пайплайн. Базовый файл можно взять из официального репозитория NVIDIA (вариант для телеком-звонков):

```bash
wget -O gpu_services/models/diar_inference.yaml \
  "https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/inference/diar_infer_telephonic.yaml"
```

Этот конфиг подойдёт и для встреч, так как сервис программно подменяет пути к .nemo-файлам. При необходимости скорректируйте параметры `collar`, `oracle_vad` или блок `speaker_embeddings` — изменения сохранятся между перезапусками.

## 4. Проверка зависимостей

1. Убедитесь, что в GPU-виртуальном окружении установлен `nemo_toolkit[asr]` и `omegaconf`. Скрипт `diarization_cpu_smoke_test.sh` проверяет это автоматически, но можно запустить вручную:
   ```bash
   gpu_services/.venv/bin/python - <<'PY'
   import nemo.collections.asr
   import omegaconf
   print('NeMo и OmegaConf доступны')
   PY
   ```
2. При необходимости доустановите `grpcio` и `protobuf` (скрипт также делает это самостоятельно):
   ```bash
   uv pip install --python gpu_services/.venv/bin/python "grpcio>=1.75.1" "protobuf>=6.31.1"
   ```

## 5. Запуск smoke-теста

1. Подготовьте аудиофайл. По умолчанию скрипт копирует `sample_dialogue.wav` в `data/raw/diarization_smoke.wav`. Можно передать собственный файл через `DIARIZATION_SMOKE_AUDIO=/path/to/file.wav`.
2. Запустите smoke-тест:
   ```bash
   ./scripts/diarization_cpu_smoke_test.sh
   ```
3. Скрипт запускает `gpu_services.diarize_service`, ожидает доступности gRPC-порта (`50052` по умолчанию), затем отправляет запрос `Run` и выводит JSON с сегментами и идентификаторами спикеров.
4. Логи сервиса пишутся в `.diarize_service.log`. При падении проверяйте этот файл на предмет сообщений NeMo (отсутствие модели, несовместимая версия PyTorch, нехватка GPU-памяти).

### Частые проблемы

- **`Missing diarization artifacts`** — убедитесь, что `diar_inference.yaml` и `.nemo`-файлы лежат в `gpu_services/models/` и доступны для чтения.
- **`RuntimeError: CUDA error`** — проверьте, что драйвер и версия CUDA совместимы, а также что на видеокарте достаточно памяти (MSDD требует ~2–3 ГБ).
- **Тест зависает на CPU** — нейросетевой декодер MSDD обрабатывает аудио заметно медленнее без CUDA. Для CPU-отладки отключите MSDD: установите переменную окружения `DIARIZATION_MSDD_MODEL_PATH=""` перед запуском скрипта.

## 6. Что подтверждено на практике

- **CPU:**
  - Развёртывание виртуального окружения `./install_deps.sh --gpu` с флагом `GPU_CUDA_VARIANT=cpu`.
  - Загрузка VAD и speaker-моделей, проверка SHA-256.
  - Старт скрипта `diarization_cpu_smoke_test.sh` до шага проверки артефактов (сервис запускается, но inference идёт крайне медленно).
- **GPU обязательно:**
  - Полное прохождение smoke-теста с генерацией сегментов в разумное время.
  - Использование MSDD для улучшения качества (на CPU декодер практически не работает).
  - Регулярное тестирование на длительных записях (CPU приводит к превышению таймаутов и перегреву).

Следуйте этому чек-листу при каждом обновлении пайплайна диаризации. При изменении требований обновляйте документ и `docs/README.md` для сохранения единого источника правды.
