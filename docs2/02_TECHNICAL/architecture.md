# Архитектура

**Дата среза:** 2026-08-31.

> **AS IS: архитектуры не существует.** В репозитории нет ни одного файла кода. Проверено: рекурсивный листинг корня содержит только `source/постановка задач.md`, `source/links.md`, `.claude/settings.local.json`. Git-репозиторий не инициализирован (`git rev-parse` → `fatal: not a git repository`).
>
> Всё ниже — целевая архитектура (TO BE) по ПЗ §16–§18, плюс явно помеченные `PROPOSAL`-фрагменты.

## Архитектурные принципы (CONFIRMED, ПЗ)

| # | Принцип | Источник |
|---|---|---|
| A-1 | Модульный последовательный pipeline, не multi-agent система | ПЗ §16 (D-001) |
| A-2 | Детерминированное — коду, семантическое — LLM. LLM не применяется к HTTP-обходу и PDF-парсингу | ПЗ §17, §18 (D-006, BR-011) |
| A-3 | Единый LLM API для четырёх задач: link relevance, document relevance, evidence extraction, synthesis | ПЗ §17 (D-004) |
| A-4 | Отказ одного источника не останавливает pipeline | ПЗ §6 (BR-001) |
| A-5 | Архитектура допускает будущее добавление исключённых из MVP возможностей, но не реализует их сейчас | ПЗ §4, §28 (REQ-033) |
| A-6 | Валидация данных на границах модулей — Pydantic | ПЗ §17 (D-007) |

## Целевая структура (ПЗ §16, D-009)

```
project/
├── app/
│   ├── crawler/
│   │   ├── fetcher.py          # HTTP-загрузка, timeouts, redirects, лимиты размера
│   │   ├── url_validator.py    # нормализация, whitelist схем, запрет private IP, проверка доступности
│   │   └── link_extractor.py   # извлечение hyperlinks и метаданных ссылки
│   ├── parsers/
│   │   ├── html_parser.py      # title, meta, headings, основной текст, снятие boilerplate
│   │   └── pdf_parser.py       # постраничный текст, число страниц, детекция скана
│   ├── discovery/
│   │   ├── link_classifier.py  # 4 класса ссылок
│   │   └── crawler.py          # рекурсия depth ≤ 2, лимиты, дедупликация
│   ├── research/
│   │   ├── relevance.py        # семантическая оценка документа
│   │   ├── evidence_extractor.py # извлечение claim + quote + source
│   │   └── synthesizer.py      # итоговый answer и Markdown-отчёт
│   ├── models/
│   │   └── schemas.py          # Pydantic-модели всех структур
│   └── main.py                 # CLI и оркестрация pipeline
├── tests/
├── data/
│   ├── raw/                    # скачанные HTML и PDF
│   └── results/                # research_result.json, research_report.md
├── config/
│   └── settings.yaml           # лимиты, параметры pipeline
├── requirements.txt
├── .env.example                # ключи LLM API
└── README.md
```

Отклонения от этой структуры требуют решения техлида — она зафиксирована как D-009.

## Компоненты и их ответственность

| Компонент | Ответственность | Требования | Исполнитель | Статус | GAP | Задача |
|---|---|---|---|---|---|---|
| `main.py` | Разбор CLI-аргументов, оркестрация стадий, запись результатов | REQ-001, REQ-022, REQ-023 | код | NOT_STARTED | GAP-001 | T-004 |
| `url_validator.py` | Нормализация URL, whitelist `http`/`https`, запрет `file://`/localhost/private IP, проверка доступности, определение `content_type` и `domain` | REQ-002, REQ-003, REQ-005, REQ-026 | код | BLOCKED | GAP-003 | T-005 |
| `fetcher.py` | HTTP-загрузка HTML и PDF, timeouts, redirects, ограничение размера ответа, сохранение в `data/raw/` | REQ-004, REQ-026 | код | BLOCKED | GAP-004 | T-006 |
| `html_parser.py` | Извлечение title, meta description, headings h1–h6, основного текста, удаление boilerplate | REQ-006, REQ-007 | код | BLOCKED | GAP-005 | T-007 |
| `link_extractor.py` | Извлечение всех hyperlinks с `source_url`, `target_url`, `anchor_text`, `extension`, `same_domain` | REQ-008 | код | BLOCKED | GAP-006 | T-008 |
| `link_classifier.py` | Классификация ссылок на `HIGH_VALUE` / `POTENTIALLY_RELEVANT` / `NAVIGATION` / `IRRELEVANT` | REQ-009 | код и/или LLM (не определено) | BLOCKED | GAP-007 | T-009 |
| `crawler.py` | Рекурсивный обход depth ≤ 2, соблюдение лимитов 20/50, дедупликация по canonical URL | REQ-010, REQ-011, REQ-012, REQ-013 | код | BLOCKED | GAP-008 | T-010 |
| `pdf_parser.py` | Постраничное извлечение текста, число страниц, детекция скана → `ocr_required` | REQ-014, REQ-015 | код | BLOCKED | GAP-009 | T-011 |
| `relevance.py` | Семантическая оценка документа: `relevance`, `score`, `reason` | REQ-016, REQ-017 | LLM | BLOCKED | GAP-010 | T-012 |
| `evidence_extractor.py` | Извлечение evidence из HIGH/MEDIUM документов | REQ-018 | LLM | BLOCKED | GAP-011 | T-013 |
| `synthesizer.py` | Итоговый `answer`, Markdown-отчёт | REQ-020, REQ-021 | LLM + код | BLOCKED | GAP-012 | T-015 |
| `models/schemas.py` | Pydantic-модели всех структур данных | REQ-019, все структуры §6–§14 | код | BLOCKED | GAP-002 | T-002 |
| Логирование | События crawler и ошибки | REQ-024 | код | NOT_STARTED | GAP-013 | T-003 |
| Кэш | Однократная загрузка URL, хранение status / timestamp / content hash / parsed text | REQ-025 | код | BLOCKED | GAP-014 | T-017 |
| LLM-клиент | Единая точка доступа к LLM API для четырёх задач | REQ-028 | код | BLOCKED | GAP-015 | T-012 |

`BLOCKED` означает наличие незакрытого открытого вопроса на критическом пути компонента — см. [as-is-gap-analysis.md](as-is-gap-analysis.md) и [status.md](../03_IMPLEMENTATION/status.md). `NOT_STARTED` — решений достаточно, работа не начата.

Компонент «LLM-клиент» в структуре ПЗ §16 отдельно не назван. Его размещение (`app/research/llm_client.py` или иное) — `PROPOSAL`, требует решения техлида ([TQ-01](questions-for-techlead.md#tq-01)).

## Поток данных

```
CLI args ──► ResearchRequest {research_question, seed_urls}
                    │
                    ▼
             url_validator ──► UrlCheckResult[]        (BR-010, BR-001)
                    │
                    ▼
                fetcher ──────► RawDocument[]          (кэш: BR-013)
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
    html_parser            pdf_parser
   ParsedPage            ParsedPdf                     (BR-009, BR-014)
          │
          ▼
   link_extractor ──────► Link[]                       (REQ-008)
          │
          ▼
   link_classifier ─────► ClassifiedLink[]             (BR-005)
          │
          ▼
      crawler  ◄── обратная связь: новые URL на depth+1 (BR-002, BR-003, BR-004)
          │
          ▼
     relevance ──────────► RelevanceAssessment[]       (BR-006, LLM)
          │  (только HIGH и MEDIUM)
          ▼
 evidence_extractor ─────► Evidence[]                  (BR-007, BR-008, LLM)
          │
          ▼
    synthesizer ─────────► ResearchResult ──► research_result.json
                                   └────────► research_report.md
```

Сквозные аспекты на всех стадиях: логирование (BR-015), кэш (BR-013), лимиты и безопасность (BR-010, BR-003).

## Ключевые технические аспекты

### Идемпотентность

ПЗ прямо не требует идемпотентности запусков. Косвенные требования: BR-004 (один canonical URL — один обход) и BR-013 (один URL — одна загрузка) обеспечивают идемпотентность **внутри одного исследования**. Идемпотентность между запусками зависит от политики кэша — [OQ-020](../01_PRODUCT/open-questions.md#oq-020). Результат LLM-стадий недетерминирован по своей природе; требования к воспроизводимости результата ПЗ не содержит.

### Хранение

`data/raw/` — скачанные материалы, `data/results/` — итоговые артефакты (ПЗ §16). Кэш — файлы или SQLite, выбор не сделан ([OQ-014](../01_PRODUCT/open-questions.md#oq-014)). Схема хранения и порядок развёртывания — [migrations-and-deployment.md](../03_IMPLEMENTATION/migrations-and-deployment.md).

### Аудит

Требование аудита в ПЗ отсутствует. Ближайшее к нему — логирование действий crawler (REQ-024, BR-015), но это диагностический лог, а не аудит действий пользователя. Аудит запусков — часть [OQ-021](../01_PRODUCT/open-questions.md#oq-021).

### Версионирование

Правил версионирования результатов, документов, кэша или схемы данных ПЗ не содержит. Не придумывать — часть [OQ-020](../01_PRODUCT/open-questions.md#oq-020) и [OQ-027](../01_PRODUCT/open-questions.md#oq-027).

### Безопасность

Исходное ПЗ §21 описывает защиту crawler от опасных целей: whitelist схем, запрет `file://`, localhost и private IP (BR-010), лимиты размера и глубины, обработка redirects, нормализация URL. Из численных значений по-прежнему не заданы timeout, max response size и max PDF size — [OQ-007](../01_PRODUCT/open-questions.md#oq-007).

**Вежливость к целевым сайтам задана Дополнением к ПЗ §21** (BR-016…BR-018, [D-046](../01_PRODUCT/decisions.md#d-046)…[D-048](../01_PRODUCT/decisions.md#d-048)): соблюдение robots.txt по RFC 9309 с fail-closed при 5xx, собственный User-Agent без маскировки, 1 запрос к host с интервалом 2 с, backoff при 429/503, запрет обхода login/CAPTCHA/paywall. Правовой статус — `legal_review_status: NOT_COMPLETED`.

Секрет системы — ключ LLM API шлюза `https://prod-litellm.nationalbank.kz/v1`; хранится в `.env`, имя переменной — в `.env.example` ([D-031](../01_PRODUCT/decisions.md#d-031)).

### Авторизация

Механизмов авторизации ПЗ не предусматривает — см. [roles-and-permissions.md](../01_PRODUCT/roles-and-permissions.md) и [OQ-021](../01_PRODUCT/open-questions.md#oq-021).

## Что архитектура сознательно не содержит

Исключено ПЗ §4 и §16: очередей и брокеров, распределённого выполнения, оркестратора агентов, векторной БД, поискового индекса, планировщика, веб-сервера, headless-браузера, слоя OCR. Добавление любого из них на этапе 1 — нарушение D-001 и A-5.
