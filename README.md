# Структура проекта

```
app/
├── main.py              # точка входа: конфиг -> сервисы -> сервер
├── config.py             # Settings, единая точка чтения/валидации env
├── logging_setup.py
├── bot.py                # сборка Dispatcher + DI + include_router
├── server.py              # aiohttp app, webhook, health-check, lifecycle
├── infra/
│   ├── redis_client.py    # только жизненный цикл соединения
│   └── rng.py              # QuantumRNG (ANU QRNG API)
├── repositories/           # один файл = один Redis-домен
│   ├── duel_repo.py
│   ├── daily_repo.py
│   ├── vote_repo.py
│   └── flip_repo.py
├── common/
│   ├── texts.py             # тексты, общие для нескольких фич
│   └── keyboards.py
└── features/                # каждая фича — независимый модуль
    ├── core/handlers.py      # /start, fallback-хендлер
    ├── flip/{handlers,texts}.py
    ├── duel/{handlers,service,texts}.py
    ├── daily/{handlers,service}.py
    ├── vote/{handlers,service,texts}.py
    └── ads/{service,texts}.py
```

## Принципы

- **Одна фича — одна папка.** Хендлеры, бизнес-логика и тексты фичи лежат рядом,
  не размазаны по общим файлам.
- **DI через `Dispatcher`.** В `bot.py` создаются репозитории/сервисы и кладутся
  в `dp["имя"] = объект`. aiogram 3 сам подставляет их в хендлеры по имени
  параметра (`async def handler(message, qrng: QuantumRNG, duel_repo: DuelRepository)`).
  Никаких глобальных синглтонов — можно подменять зависимости в тестах.
- **Repositories = только Redis-запросы**, без бизнес-логики. Бизнес-логика
  (генерация id, подсчёт голосов, тай-брейк) — в `service.py` фичи.
- **Конфиг читается один раз** в `config.py::load_settings()`, при ошибке —
  явное исключение `ConfigError`, а не разбросанные по коду `sys.exit(1)`.

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env  # и заполнить
python main.py
```

## Новое по сравнению с предыдущей версией

- Добавлены рабочие хендлеры `/vote` (раньше была только инфраструктура в БД,
  без единого хендлера).
- Счётчик подбрасываний для рекламы перенесён из памяти процесса в Redis
  (`repositories/flip_repo.py`) — переживает рестарт на Render.
- `QuantumRNG._pool` больше не читается напрямую снаружи — добавлены свойства
  `pool_size` и `refill_threshold`.
