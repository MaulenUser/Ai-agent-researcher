# Анализ расхождений AS IS / TO BE

**Дата среза:** 2026-08-31.

## Метод и доказательная база

Утверждения AS IS в этом документе опираются на **один проверенный факт**: исполняемого кода в репозитории не существует.

**Доказательство (выполнено 2026-08-31):**

| Проверка | Команда | Результат |
|---|---|---|
| Полный рекурсивный листинг репозитория | `Get-ChildItem -Force -Recurse C:\Users\Fs_azamat_t_inet\Desktop\macroprud` | 5 объектов: каталоги `.claude`, `source`; файлы `.claude\settings.local.json` (74 Б), `source\links.md` (11 016 Б), `source\постановка задач.md` (19 214 Б) |
| Наличие git-истории | `git rev-parse --abbrev-ref HEAD` | `fatal: not a git repository (or any of the parent directories): .git` |
| Версия интерпретатора | `python --version` | `Python 3.10.0` |

Из этого следует: нет каталогов `app/`, `tests/`, `data/`, `config/`; нет файлов `requirements.txt`, `.env.example`, `README.md`; нет ни одного `.py`-файла; нет миграций; нет тестов; нет commit и ветки, на которые можно сослаться.

**Следствия для формы таблицы.** Колонка «AS IS» во всех строках содержит `Отсутствует`. Колонка «Доказательство» ссылается на приведённые выше проверки, а не на файлы и функции — ссылаться не на что. Статусов `PARTIAL`, `LEGACY-AS-IS` и `REUSABLE` в реестре нет, поскольку не существует ни частичной, ни устаревшей, ни переиспользуемой реализации.

**Тесты не запускались** — запускать нечего. Историческими результатами прогонов документация не располагает.

## Реестр расхождений

| GAP | Требование | AS IS | TO BE | Статус | Доказательство | Что делать |
|---|---|---|---|---|---|---|
| GAP-001 | REQ-001, REQ-022, REQ-023 | Отсутствует | CLI `python -m app.main --question ... --urls urls.json`, оркестрация pipeline, запись `data/results/research_result.json` и `research_report.md` | BLOCKED | Листинг репозитория: `app/main.py` не существует | Закрыть [OQ-015](../01_PRODUCT/open-questions.md#oq-015) (формат `urls.json`), затем T-004, T-016 |
| GAP-002 | REQ-032, REQ-033, REQ-035 | Отсутствует | Каркас проекта по структуре ПЗ §16, зависимости (`httpx`, `bs4`, `lxml`, `PyMuPDF`, `Pydantic`), Pydantic-схемы всех сущностей | BLOCKED | Нет `app/`, `requirements.txt`, `app/models/schemas.py`. `python --version` = 3.10.0 против требуемого 3.11+ | Закрыть [OQ-019](../01_PRODUCT/open-questions.md#oq-019) и [OQ-027](../01_PRODUCT/open-questions.md#oq-027), затем T-001, T-002 |
| GAP-003 | REQ-002, REQ-003, REQ-005 | Отсутствует | `url_validator.py`: нормализация, whitelist схем, запрет private IP, проверка доступности, `status` / `http_status` / `final_url` / `content_type` / `domain` | BLOCKED | Нет `app/crawler/url_validator.py` | Закрыть [OQ-024](../01_PRODUCT/open-questions.md#oq-024), [OQ-013](../01_PRODUCT/open-questions.md#oq-013), [OQ-025](../01_PRODUCT/open-questions.md#oq-025), затем T-005 |
| GAP-004 | REQ-004, REQ-026 | Отсутствует | `fetcher.py`: загрузка HTML и PDF, timeouts, редиректы, лимиты размера, robots.txt и rate limiting (BR-016…BR-018), сохранение в `data/raw/` | BLOCKED | Нет `app/crawler/fetcher.py` | Закрыть остаток [OQ-007](../01_PRODUCT/open-questions.md#oq-007) (timeout и предельные размеры) и [OQ-025](../01_PRODUCT/open-questions.md#oq-025), затем T-006. OQ-008 закрыт 2026-08-31 |
| GAP-005 | REQ-006, REQ-007 | Отсутствует | `html_parser.py`: title, meta description, headings h1–h6, основной текст без boilerplate | BLOCKED | Нет `app/parsers/html_parser.py` | Закрыть [OQ-018](../01_PRODUCT/open-questions.md#oq-018), [OQ-016](../01_PRODUCT/open-questions.md#oq-016), затем T-007 |
| GAP-006 | REQ-008 | Отсутствует | `link_extractor.py`: все hyperlinks с `source_url`, `target_url`, `anchor_text`, `extension`, `same_domain` | BLOCKED | Нет `app/crawler/link_extractor.py` | Закрыть [OQ-013](../01_PRODUCT/open-questions.md#oq-013), затем T-008 |
| GAP-007 | REQ-009 | Отсутствует | `link_classifier.py` + `config/link_taxonomy.yaml`: 4 класса + `UNKNOWN` по BR-005 и [link-taxonomy.md](../01_PRODUCT/link-taxonomy.md) | **NOT_STARTED** (разблокировано 2026-08-31) | Нет `app/discovery/link_classifier.py` | Блокирующих OQ нет. Выполнять T-009; интеграция ждёт T-008 |
| GAP-008 | REQ-010, REQ-011, REQ-012, REQ-013 | Отсутствует | `crawler.py`: рекурсия depth ≤ 2, лимиты 20/50, дедупликация по canonical URL | BLOCKED | Нет `app/discovery/crawler.py` | Закрыть [OQ-025](../01_PRODUCT/open-questions.md#oq-025) и продуктовое решение по поведению на лимите (BR-003), затем T-010 |
| GAP-009 | REQ-014, REQ-015 | Отсутствует | `pdf_parser.py`: постраничный текст, число страниц, детекция скана → `ocr_required` | BLOCKED | Нет `app/parsers/pdf_parser.py` | Закрыть [OQ-017](../01_PRODUCT/open-questions.md#oq-017), затем T-011 |
| GAP-010 | REQ-016, REQ-017 | Отсутствует | `relevance.py`: семантическая оценка `relevance` / `score` / `reason` | BLOCKED | Нет `app/research/relevance.py` | Закрыть [OQ-003](../01_PRODUCT/open-questions.md#oq-003), [OQ-006](../01_PRODUCT/open-questions.md#oq-006), [OQ-028](../01_PRODUCT/open-questions.md#oq-028), затем T-012. OQ-001 закрыт 2026-08-31 |
| GAP-011 | REQ-018 | Отсутствует | `evidence_extractor.py`: evidence из HIGH/MEDIUM с обязательным `source_url` | BLOCKED | Нет `app/research/evidence_extractor.py` | Закрыть [OQ-004](../01_PRODUCT/open-questions.md#oq-004), [OQ-005](../01_PRODUCT/open-questions.md#oq-005), затем T-013 |
| GAP-012 | REQ-019, REQ-020, REQ-021 | Отсутствует | JSON-вывод по ПЗ §14, Markdown-отчёт по ПЗ §15, итоговый `answer` | BLOCKED | Нет `app/research/synthesizer.py`, нет `data/results/` | Закрыть [OQ-027](../01_PRODUCT/open-questions.md#oq-027) (конфликт C-007) и [OQ-011](../01_PRODUCT/open-questions.md#oq-011), затем T-014, T-015 |
| GAP-013 | REQ-024 | Отсутствует | Логирование всех действий crawler и ошибок в формате ПЗ §19 | NOT_STARTED | Нет кода и конфигурации логирования | T-003 — блокеров нет, можно делать сразу |
| GAP-014 | REQ-025 | Отсутствует | Кэш: однократная загрузка URL, хранение URL / timestamp / status / content hash / parsed text | BLOCKED | Нет реализации кэша, нет `data/` | Закрыть [OQ-014](../01_PRODUCT/open-questions.md#oq-014), [OQ-020](../01_PRODUCT/open-questions.md#oq-020), [OQ-025](../01_PRODUCT/open-questions.md#oq-025), затем T-017 |
| GAP-015 | REQ-027, REQ-028 | Отсутствует | Единый LLM-клиент для четырёх задач; детерминированные задачи вне LLM | BLOCKED | Нет клиента, нет `.env.example`. Провайдер выбран 2026-08-31 ([D-031](../01_PRODUCT/decisions.md#d-031)), кода по-прежнему нет | Закрыть [OQ-006](../01_PRODUCT/open-questions.md#oq-006), [OQ-028](../01_PRODUCT/open-questions.md#oq-028), [TQ-03](questions-for-techlead.md#tq-03), затем T-012, T-013 |
| GAP-016 | REQ-029, REQ-030, REQ-031, REQ-034 | Отсутствует | Тестовый датасет ≥ 10 seed URL (ES/CZ/HU), 4 тестовых вопроса, обязательный интеграционный тест CNB SyRB, приёмочные проверки AC-01…AC-13 | BLOCKED | Нет `tests/`, ни одного теста, датасет не утверждён | Закрыть [OQ-010](../01_PRODUCT/open-questions.md#oq-010), [OQ-009](../01_PRODUCT/open-questions.md#oq-009), [OQ-022](../01_PRODUCT/open-questions.md#oq-022), затем T-018, T-019 |

Итого: 16 расхождений. `BLOCKED` — 15, `NOT_STARTED` — 1 (GAP-013). `DONE`, `PARTIAL`, `IN_PROGRESS`, `REUSABLE`, `LEGACY-AS-IS` — 0.

## Расхождения, не связанные с кодом

| GAP | Предмет | AS IS | TO BE | Статус | Доказательство | Что делать |
|---|---|---|---|---|---|---|
| GAP-017 | Управление версиями исходного кода | Git-репозиторий не инициализирован; истории изменений нет | Репозиторий с историей, ветками и возможностью ссылаться на commit при описании AS IS | NOT_STARTED | `git rev-parse --abbrev-ref HEAD` → `fatal: not a git repository` | Часть T-001. Без этого требование «указывать commit/ветку как доказательство» невыполнимо |
| GAP-018 | Процесс управления требованиями | Один файл ПЗ без версии, даты утверждения и владельца; каналы уточнений отсутствуют | Утверждённая версия ПЗ + фиксируемые письменные уточнения (приоритеты источников 2 и 3) | BLOCKED | `source/постановка задач.md` не содержит блока версии; иных документов требований в репозитории нет | Закрыть [OQ-023](../01_PRODUCT/open-questions.md#oq-023) — блокирует ответы на остальные 26 вопросов |

## Сводка по критическому пути

Разработку блокируют вопросы приоритета P1: [OQ-006](../01_PRODUCT/open-questions.md#oq-006), [OQ-007](../01_PRODUCT/open-questions.md#oq-007) (сузился), [OQ-019](../01_PRODUCT/open-questions.md#oq-019), [OQ-023](../01_PRODUCT/open-questions.md#oq-023), [OQ-025](../01_PRODUCT/open-questions.md#oq-025), [OQ-029](../01_PRODUCT/open-questions.md#oq-029). Закрыты 2026-08-31 и из списка исключены: OQ-001, OQ-002, OQ-003, OQ-008, OQ-012. Заведённые взамен OQ-028 и OQ-030 имеют приоритет P2.

Работы, которые можно начать **до** получения оставшихся ответов: T-001 (каркас проекта, кроме выбора версии Python), T-003 (логирование), **T-009** (справочник таксономии, evaluation dataset и классификатор как чистая функция), частично T-018 (инфраструктура фикстур) и T-016 (три блока конфигурации и `.env.example`). Порядок — [roadmap.md](../03_IMPLEMENTATION/roadmap.md).

## Предложения, не являющиеся решениями

Помечены `PROPOSAL` и требуют утверждения техлидом, а не самостоятельного принятия:

| PROPOSAL | Где описан |
|---|---|
| Перечень состояний URL и документа | [state-machine.md](state-machine.md#proposal-жизненный-цикл-url) |
| Сущность `RawDocument` и её поля | [domain-model.md](domain-model.md#rawdocument) |
| Размещение модуля LLM-клиента вне структуры ПЗ §16 | [questions-for-techlead.md](questions-for-techlead.md#tq-01) |
| Схема хранения кэша | [migrations-and-deployment.md](../03_IMPLEMENTATION/migrations-and-deployment.md) |
