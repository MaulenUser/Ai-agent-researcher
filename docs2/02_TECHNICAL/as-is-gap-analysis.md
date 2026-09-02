# Анализ расхождений AS IS / TO BE

**Дата среза:** 2026-09-02. **Ветка:** `main`. **Commit:** `b53c391`.

## Метод и доказательная база

С 2026-09-01 код существует, и AS IS больше не выводится из его отсутствия. Утверждения ниже опираются на чтение файлов коммита `b53c391` и на фактически запущенные проверки.

**Доказательство (выполнено 2026-09-02):**

| Проверка | Команда | Результат |
|---|---|---|
| Наличие git-истории | `git log --oneline` | `b53c391` (прототип конвейера), `3943f2a` (initial commit). Ветка `main`, remote `origin` = `https://github.com/MaulenUser/Ai-agent-researcher.git`, `origin/main` = `3943f2a` |
| Состав кода | `wc -l app/*.py tests/*.py config/*.yaml` | 5 модулей `app/` (377 строк), 2 файла тестов (228 строк), `config/link_taxonomy.yaml` (123 строки) |
| Прогон тестов | `py -3.10 -m pytest -q` | **48 passed** |
| Прогон тестов интерпретатором по умолчанию | `python -m pytest -q` | **`ModuleNotFoundError: No module named 'yaml'`** — `.venv/` в корне это Python 3.14.2 без зависимостей |
| Доступные интерпретаторы | `py -0p` | `.venv` (default) 3.14.2; глобальные 3.14 и 3.10. Зависимости установлены только в 3.10 |

**Следствия для формы таблицы.** Появились статусы `PARTIAL`. Колонка «Доказательство» ссылается на файлы и строки. Статусы `DONE`, `LEGACY-AS-IS` и `REUSABLE` по-прежнему не встречаются: ни одна задача не удовлетворяет своим критериям готовности целиком.

**Важная оговорка.** Наличие поведения в коде **не** означает, что это целевое требование: T-006, T-007, T-008 реализованы поверх незакрытых OQ, а четыре правила классификации выбраны разработчиком вместо БА ([OQ-031](../01_PRODUCT/open-questions.md#oq-031)…[OQ-034](../01_PRODUCT/open-questions.md#oq-034)). Полный разбор — [status.md](../03_IMPLEMENTATION/status.md).

**Приёмочные проверки AC-01…AC-13 не запускались** — pipeline не собран.

## Реестр расхождений

| GAP | Требование | AS IS | TO BE | Статус | Доказательство | Что делать |
|---|---|---|---|---|---|---|
| GAP-001 | REQ-001, REQ-022, REQ-023 | `app/main.py` существует, но это прототип: URL задан константой, вывод в stdout, аргументов нет, файлы не пишутся | CLI `python -m app.main --question ... --urls urls.json`, оркестрация pipeline, запись `data/results/research_result.json` и `research_report.md` | BLOCKED | `app/main.py:10` — константа `URL`; `data/results/` содержит только `.gitkeep` | Закрыть [OQ-015](../01_PRODUCT/open-questions.md#oq-015) (формат `urls.json`), затем T-004, T-016 |
| GAP-002 | REQ-032, REQ-033, REQ-035 | Каркас есть, но плоский: `app/fetcher.py`, `app/html_parser.py`, `app/link_extractor.py`, `app/taxonomy.py`, `app/main.py`. Pydantic-схем нет | Каркас проекта по структуре ПЗ §16, зависимости (`httpx`, `bs4`, `lxml`, `PyMuPDF`, `Pydantic`), Pydantic-схемы всех сущностей | **PARTIAL** | `regulatory-research-agent/app/` — нет `crawler/`, `parsers/`, `discovery/`, `models/`, `research/`, `data/raw/`. В `requirements.txt` нет `PyMuPDF` и `pydantic`. Рабочий интерпретатор — 3.10 против требуемого 3.11+ | Довести T-001 (структура и зависимости), затем T-002 после [OQ-027](../01_PRODUCT/open-questions.md#oq-027). Версия Python — [OQ-019](../01_PRODUCT/open-questions.md#oq-019) |
| GAP-003 | REQ-002, REQ-003, REQ-005 | Отсутствует | `url_validator.py`: нормализация, whitelist схем, запрет private IP, проверка доступности, `status` / `http_status` / `final_url` / `content_type` / `domain` | BLOCKED | Нет `app/crawler/url_validator.py` | Закрыть [OQ-024](../01_PRODUCT/open-questions.md#oq-024), [OQ-013](../01_PRODUCT/open-questions.md#oq-013), [OQ-025](../01_PRODUCT/open-questions.md#oq-025), затем T-005 |
| GAP-004 | REQ-004, REQ-026 | `app/fetcher.py`: httpx async, редиректы, `final_url`, `truststore.SSLContext`. Ни robots.txt, ни задержек, ни retry, ни лимитов размера, ни `data/raw/` | `fetcher.py`: загрузка HTML и PDF, timeouts, редиректы, лимиты размера, robots.txt и rate limiting (BR-016…BR-018), сохранение в `data/raw/` | **PARTIAL**, блокеры не сняты | `app/fetcher.py:15` — `timeout=20.0` в коде; `app/fetcher.py:17` — User-Agent `regulatory-research-agent/0.1` вместо `RegulatoryResearchBot/0.1` (BR-016); robots.txt в файле не упоминается | Закрыть остаток [OQ-007](../01_PRODUCT/open-questions.md#oq-007) и [OQ-025](../01_PRODUCT/open-questions.md#oq-025), затем довести T-006. **До этого реальные прогоны не проводить** — BR-016/BR-017 нарушаются |
| GAP-005 | REQ-006, REQ-007 | `app/html_parser.py`: title, заголовки, основной текст через trafilatura. Без `meta description`, без фолбэка | `html_parser.py`: title, meta description, headings h1–h6, основной текст без boilerplate | **PARTIAL**, блокеры не сняты | `app/html_parser.py` (33 строки) — `ParsedPage` по ПЗ §7 не собирается | Закрыть [OQ-018](../01_PRODUCT/open-questions.md#oq-018), [OQ-016](../01_PRODUCT/open-questions.md#oq-016), затем довести T-007 |
| GAP-006 | REQ-008 | `app/link_extractor.py`: все `<a href>`, абсолютизация, `normalize_url`, дедуп, `in_nav` + ближайший heading | `link_extractor.py`: все hyperlinks с `source_url`, `target_url`, `anchor_text`, `extension`, `same_domain` | **PARTIAL**, блокер не снят | `app/link_extractor.py:57-63` — поля `url`, `anchor_text`, `same_domain`, `in_nav`, `context`; `source_url`, `target_url`, `extension` отсутствуют. `app/link_extractor.py:60` — `same_domain` выбран разработчиком при открытом [OQ-013](../01_PRODUCT/open-questions.md#oq-013) | Закрыть OQ-013, затем довести T-008 до полей ПЗ §8 и `surrounding_text` (D-039) |
| GAP-007 | REQ-009 | `app/taxonomy.py` + `config/link_taxonomy.yaml`: 5 классов, `matches_keyword` по границам токенов, `reason` у каждой ссылки, 48 тестов | `link_classifier.py` + `config/link_taxonomy.yaml`: 4 класса + `UNKNOWN` по BR-005 и [link-taxonomy.md](../01_PRODUCT/link-taxonomy.md) | **PARTIAL** | `app/taxonomy.py:169` — класс `OTHER` вместо `UNKNOWN` (D-036); `app/taxonomy.py:31` — `STOPWORDS` в коде вопреки T-009 крит. 5; нет лога id правила и evaluation dataset (D-040) | Довести T-009 до критериев. Отдельно — вынести на БА [OQ-031](../01_PRODUCT/open-questions.md#oq-031)…[OQ-034](../01_PRODUCT/open-questions.md#oq-034) |
| GAP-008 | REQ-010, REQ-011, REQ-012, REQ-013 | Отсутствует | `crawler.py`: рекурсия depth ≤ 2, лимиты 20/50, дедупликация по canonical URL | BLOCKED | Нет `app/discovery/crawler.py` | Закрыть [OQ-025](../01_PRODUCT/open-questions.md#oq-025) и продуктовое решение по поведению на лимите (BR-003), затем T-010 |
| GAP-009 | REQ-014, REQ-015 | Отсутствует | `pdf_parser.py`: постраничный текст, число страниц, детекция скана → `ocr_required` | BLOCKED | Нет `app/parsers/pdf_parser.py` | Закрыть [OQ-017](../01_PRODUCT/open-questions.md#oq-017), затем T-011 |
| GAP-010 | REQ-016, REQ-017 | Отсутствует | `relevance.py`: семантическая оценка `relevance` / `score` / `reason` | BLOCKED | Нет `app/research/relevance.py` | Закрыть [OQ-003](../01_PRODUCT/open-questions.md#oq-003), [OQ-006](../01_PRODUCT/open-questions.md#oq-006), [OQ-028](../01_PRODUCT/open-questions.md#oq-028), затем T-012. OQ-001 закрыт 2026-08-31 |
| GAP-011 | REQ-018 | Отсутствует | `evidence_extractor.py`: evidence из HIGH/MEDIUM с обязательным `source_url` | BLOCKED | Нет `app/research/evidence_extractor.py` | Закрыть [OQ-004](../01_PRODUCT/open-questions.md#oq-004), [OQ-005](../01_PRODUCT/open-questions.md#oq-005), затем T-013 |
| GAP-012 | REQ-019, REQ-020, REQ-021 | Отсутствует | JSON-вывод по ПЗ §14, Markdown-отчёт по ПЗ §15, итоговый `answer` | BLOCKED | Нет `app/research/synthesizer.py`, нет `data/results/` | Закрыть [OQ-027](../01_PRODUCT/open-questions.md#oq-027) (конфликт C-007) и [OQ-011](../01_PRODUCT/open-questions.md#oq-011), затем T-014, T-015 |
| GAP-013 | REQ-024 | Отсутствует | Логирование всех действий crawler и ошибок в формате ПЗ §19 | NOT_STARTED | Нет кода и конфигурации логирования | T-003 — блокеров нет, можно делать сразу |
| GAP-014 | REQ-025 | Отсутствует | Кэш: однократная загрузка URL, хранение URL / timestamp / status / content hash / parsed text | BLOCKED | Нет реализации кэша, нет `data/` | Закрыть [OQ-014](../01_PRODUCT/open-questions.md#oq-014), [OQ-020](../01_PRODUCT/open-questions.md#oq-020), [OQ-025](../01_PRODUCT/open-questions.md#oq-025), затем T-017 |
| GAP-015 | REQ-027, REQ-028 | Отсутствует | Единый LLM-клиент для четырёх задач; детерминированные задачи вне LLM | BLOCKED | Нет клиента, нет `.env.example`. Провайдер выбран 2026-08-31 ([D-031](../01_PRODUCT/decisions.md#d-031)), кода по-прежнему нет | Закрыть [OQ-006](../01_PRODUCT/open-questions.md#oq-006), [OQ-028](../01_PRODUCT/open-questions.md#oq-028), [TQ-03](questions-for-techlead.md#tq-03), затем T-012, T-013 |
| GAP-016 | REQ-029, REQ-030, REQ-031, REQ-034 | 48 unit-тестов на синтетических данных (`tests/test_link_extractor.py`, `tests/test_taxonomy.py`). Офлайн-фикстур, seed-датасета и приёмочных тестов нет | Тестовый датасет ≥ 10 seed URL (ES/CZ/HU), 4 тестовых вопроса, обязательный интеграционный тест CNB SyRB, приёмочные проверки AC-01…AC-13 | BLOCKED | Нет `tests/fixtures/`, ни одного интеграционного теста; датасет не утверждён | Закрыть [OQ-010](../01_PRODUCT/open-questions.md#oq-010), [OQ-009](../01_PRODUCT/open-questions.md#oq-009), [OQ-022](../01_PRODUCT/open-questions.md#oq-022), затем T-018, T-019 |

Итого: 16 расхождений. `PARTIAL` — 5 (GAP-002, GAP-004, GAP-005, GAP-006, GAP-007), `BLOCKED` — 10, `NOT_STARTED` — 1 (GAP-013). `DONE`, `IN_PROGRESS`, `REUSABLE`, `LEGACY-AS-IS` — 0.

**Новое расхождение, не имевшее аналога до появления кода:**

| GAP | Требование | AS IS | TO BE | Статус | Доказательство | Что делать |
|---|---|---|---|---|---|---|
| GAP-019 | ПЗ §16 (`.env.example`), T-016 крит. 2 | `.env.example` содержал **реальный** `LLM_API_KEY`; файл закоммичен в `3943f2a` и запушен в `origin/main` | `.env.example` содержит только имена переменных без значений | **PARTIAL** | `git cat-file -p b30365d` — блоб коммита `3943f2a` со строкой `LLM_API_KEY=sk-vhac…`; `.git/refs/remotes/origin/main` = `3943f2a` | **Отозвать и перевыпустить ключ.** Значение удалено из файла 2026-09-02, но из истории и с GitHub этим не исчезает |

## Расхождения, не связанные с кодом

| GAP | Предмет | AS IS | TO BE | Статус | Доказательство | Что делать |
|---|---|---|---|---|---|---|
| GAP-017 | Управление версиями исходного кода | Репозиторий инициализирован, ветка `main`, два коммита, remote `origin` настроен. Код закоммичен 2026-09-02 (`b53c391`) — сутки пролежал untracked | Репозиторий с историей, ветками и возможностью ссылаться на commit при описании AS IS | **DONE** | `git log --oneline` → `b53c391`, `3943f2a`; `git remote -v` → `origin` | Закрыто. Требование «указывать commit как доказательство AS IS» с 2026-09-02 выполнимо и применяется в этом документе |
| GAP-018 | Процесс управления требованиями | Один файл ПЗ без версии, даты утверждения и владельца; каналы уточнений отсутствуют | Утверждённая версия ПЗ + фиксируемые письменные уточнения (приоритеты источников 2 и 3) | BLOCKED | `source/постановка задач.md` не содержит блока версии; иных документов требований в репозитории нет | Закрыть [OQ-023](../01_PRODUCT/open-questions.md#oq-023) — блокирует ответы на остальные 26 вопросов |

## Сводка по критическому пути

Разработку блокируют вопросы приоритета P1: [OQ-006](../01_PRODUCT/open-questions.md#oq-006), [OQ-007](../01_PRODUCT/open-questions.md#oq-007) (сузился), [OQ-019](../01_PRODUCT/open-questions.md#oq-019), [OQ-023](../01_PRODUCT/open-questions.md#oq-023), [OQ-025](../01_PRODUCT/open-questions.md#oq-025), [OQ-029](../01_PRODUCT/open-questions.md#oq-029). Закрыты 2026-08-31 и из списка исключены: OQ-001, OQ-002, OQ-003, OQ-008, OQ-012. Заведённые взамен OQ-028 и OQ-030 имеют приоритет P2.

Работы, которые можно вести **до** получения оставшихся ответов (обновлено 2026-09-02): отзыв утёкшего ключа и починка окружения (venv + зависимости); T-003 (логирование); доведение **T-009** до критериев (`UNKNOWN` вместо `OTHER`, `STOPWORDS` в YAML, лог id правила, evaluation dataset); доведение T-001 (структура ПЗ §16, `requirements.txt` по D-007); частично T-018 (инфраструктура фикстур) и T-016 (три блока конфигурации). Порядок — [roadmap.md](../03_IMPLEMENTATION/roadmap.md).

**Отдельно:** T-006, T-007, T-008 уже имеют код, но их блокеры не сняты. Расширять эти модули до ответов на OQ-007, OQ-013, OQ-016, OQ-018, OQ-025 нельзя — каждое дополнение закрепит непринятое поведение.

## Предложения, не являющиеся решениями

Помечены `PROPOSAL` и требуют утверждения техлидом, а не самостоятельного принятия:

| PROPOSAL | Где описан |
|---|---|
| Перечень состояний URL и документа | [state-machine.md](state-machine.md#proposal-жизненный-цикл-url) |
| Сущность `RawDocument` и её поля | [domain-model.md](domain-model.md#rawdocument) |
| Размещение модуля LLM-клиента вне структуры ПЗ §16 | [questions-for-techlead.md](questions-for-techlead.md#tq-01) |
| Схема хранения кэша | [migrations-and-deployment.md](../03_IMPLEMENTATION/migrations-and-deployment.md) |
