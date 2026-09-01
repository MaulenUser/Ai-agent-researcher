# Доменная модель

**Дата среза:** 2026-08-31.

> **AS IS: моделей не существует.** Файла `app/models/schemas.py` нет, как и всего каталога `app/`. Ни одной Pydantic-модели в репозитории не определено.
>
> Ниже — сущности, **выведенные из примеров JSON в ПЗ**. ПЗ приводит примеры, а не схемы: типы, обязательность и допустимые значения полей в нём почти нигде не заданы. Пометка «не задано» означает, что значение нельзя выбрать самостоятельно ([OQ-027](../01_PRODUCT/open-questions.md#oq-027)).

## Обзор сущностей

```
ResearchRequest
   │ 1..*
   ▼
SeedUrl ──► UrlCheckResult ──► RawDocument
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
                ParsedPage                   ParsedPdf
                     │ 1..*                       │ 1..*
                     ▼                            ▼
                   Link                        PdfPage
                     │
                     ▼
              ClassifiedLink ──► (новый SeedUrl на depth+1)

RawDocument ──► RelevanceAssessment ──► Evidence
                                            │
                                            ▼
                                     ResearchResult
```

Связи: одно исследование → много seed URL → каждый порождает дерево документов глубиной ≤ 2 (BR-002); документ → одна оценка релевантности; документ HIGH/MEDIUM → 0..N evidence (BR-006); исследование → один `ResearchResult`.

---

## ResearchRequest

Вход системы. Источник: ПЗ §3, §27; REQ-001, REQ-022.

| Поле | Тип | Обязательность | Источник | Примечание |
|---|---|---|---|---|
| `research_question` | string | обязательно | ПЗ §3 | Ограничений на длину и язык нет |
| `seed_urls` | string[] | обязательно | ПЗ §3 | Минимальное и максимальное количество не задано |

Формат файла `urls.json`, из которого читается запрос, не определён — [OQ-015](../01_PRODUCT/open-questions.md#oq-015). ПЗ §3 показывает единый объект с обоими полями, а ПЗ §27 — раздельную передачу вопроса (`--question`) и URL (`--urls`). Согласование — часть OQ-015.

## UrlCheckResult

Результат проверки доступности. Источник: ПЗ §6; REQ-002, REQ-003, REQ-005.

| Поле | Тип | Обязательность | Источник | Примечание |
|---|---|---|---|---|
| `url` | string | обязательно | ПЗ §6 | Исходный URL |
| `status` | enum | обязательно | ПЗ §6 | В ПЗ показано только `"accessible"`. Закрытый перечень не задан — [OQ-024](../01_PRODUCT/open-questions.md#oq-024) |
| `http_status` | int | не задано | ПЗ §6 | Отсутствует при timeout и SSL error — поведение не описано |
| `final_url` | string | не задано | ПЗ §6 | URL после редиректов |
| `content_type` | string | не задано | ПЗ §6 | Пример: `text/html` |
| `domain` | string | не задано | ПЗ §6 | Правило вычисления при редиректе не задано — [OQ-013](../01_PRODUCT/open-questions.md#oq-013) |

Обрабатываемые ситуации по ПЗ §6: HTTP 200, redirect, 404, 403, timeout, SSL error, unsupported content type. Соответствие ситуаций значениям `status` в ПЗ отсутствует. См. [state-machine.md](state-machine.md).

## RawDocument

Загруженный материал до разбора. Источник: **выведена**, в ПЗ как отдельная сущность не описана; необходима для REQ-004, REQ-025 и `data/raw/` (ПЗ §16).

**Статус: `PROPOSAL`.** Состав полей опирается на перечень кэша из ПЗ §20 (URL, fetch timestamp, status, content hash, parsed text) и на поля `discovered_documents[]` из ПЗ §14 (`title`, `url`, `type`, `depth`, `relevance`). Подтверждение — [TQ-02](questions-for-techlead.md#tq-02).

| Поле | Тип | Источник |
|---|---|---|
| `url` | string | ПЗ §20 |
| `final_url` | string | ПЗ §6 |
| `type` | enum: `html` \| `pdf` | ПЗ §14 (`"type": "pdf"`, `"type": "html"`) |
| `depth` | int (0..2) | ПЗ §10, §14 |
| `fetched_at` | datetime | ПЗ §20 («fetch timestamp») |
| `content_hash` | string | ПЗ §20 |
| `local_path` | string | Выведено из наличия `data/raw/` (ПЗ §16) — PROPOSAL |
| `status` | enum | ПЗ §20; для PDF-сканов — `ocr_required` (ПЗ §11) |

## ParsedPage

Разобранная HTML-страница. Источник: ПЗ §7; REQ-006, REQ-007.

| Поле | Тип | Обязательность | Источник |
|---|---|---|---|
| `title` | string | не задано | ПЗ §7 |
| `meta_description` | string | не задано | ПЗ §7 (в примере JSON отсутствует, в тексте требования присутствует) |
| `headings` | string[] | не задано | ПЗ §7 — заголовки h1–h6. В примере — плоский список без уровня заголовка |
| `text` | string | не задано | ПЗ §7 — основной текст без boilerplate |
| `links` | Link[] | не задано | ПЗ §7 — в примере укороченная форма `{anchor, url}` |

Расхождение форм ссылки в §7 (`{anchor, url}`) и §8 (пять полей) — §7 показывает вложенную проекцию, §8 — полную сущность. Это трактовка, не утверждённое решение; относится к [OQ-027](../01_PRODUCT/open-questions.md#oq-027).

Сохраняется ли уровень заголовка (h1 против h3) — из ПЗ не следует.

## ParsedPdf

Разобранный PDF. Источник: ПЗ §11; REQ-014, REQ-015.

| Поле | Тип | Обязательность | Источник |
|---|---|---|---|
| `url` | string | не задано | ПЗ §11 |
| `title` | string | не задано | ПЗ §11. Источник заголовка (метаданные PDF, anchor text ссылки, первая строка) не указан |
| `pages` | PdfPage[] | не задано | ПЗ §11 |
| `status` | enum | условно | ПЗ §11 — `ocr_required` для сканов (BR-009) |

Количество страниц требуется определять (REQ-014); отдельного поля в примере ПЗ §11 нет — выводится из длины `pages`.

### PdfPage

| Поле | Тип | Источник |
|---|---|---|
| `page` | int | ПЗ §11. Нумерация в примере начинается с 1 |
| `text` | string | ПЗ §11 |

## Link

Извлечённая ссылка. Источник: ПЗ §8; REQ-008.

| Поле | Тип | Обязательность | Источник | Примечание |
|---|---|---|---|---|
| `source_url` | string | не задано | ПЗ §8 | Страница, на которой найдена ссылка |
| `target_url` | string | не задано | ПЗ §8 | Абсолютный или относительный — не уточнено |
| `anchor_text` | string | не задано | ПЗ §8 | Поведение при пустом anchor (ссылка-картинка) не описано |
| `extension` | string | не задано | ПЗ §8 | Пример: `pdf`. Значение при отсутствии расширения не задано |
| `same_domain` | bool | не задано | ПЗ §8 | Правило вычисления — [OQ-013](../01_PRODUCT/open-questions.md#oq-013) |
| `context` | LinkContext | обязательно | Ответ БА 2026-08-31, [D-039](../01_PRODUCT/decisions.md#d-039) | **Добавлено 2026-08-31.** В ПЗ §8 отсутствует; сделано обязательным ответом БА, поскольку классификатор обязан учитывать окружение ссылки |

### LinkContext (добавлено 2026-08-31)

| Поле | Тип | Источник | Примечание |
|---|---|---|---|
| `surrounding_text` | string | [D-039](../01_PRODUCT/decisions.md#d-039) | Текст родительского блочного контейнера |
| `section_heading` | string | [D-039](../01_PRODUCT/decisions.md#d-039) | Ближайший предшествующий заголовок h1–h6 |
| `dom_container` | enum: `nav` \| `header` \| `footer` \| `main` \| `aside` \| `table` \| `list` \| `body` | [D-039](../01_PRODUCT/decisions.md#d-039) | Ближайший семантический контейнер; определяет применимость правила P-3 |

Расширение ПЗ §8, а не противоречие: §8 приводит пример JSON, не схему, и `Link` в выходной контракт §14 не входит. Заполнение — задача T-008.

## ClassifiedLink

Ссылка с присвоенным классом. Источник: ПЗ §9, ответ БА 2026-08-31; REQ-009, BR-005.

| Поле | Тип | Источник | Примечание |
|---|---|---|---|
| `link` | Link | ПЗ §8 | |
| `link_class` | enum: `HIGH_VALUE` \| `POTENTIALLY_RELEVANT` \| `NAVIGATION` \| `IRRELEVANT` \| `UNKNOWN` | ПЗ §9 + [D-036](../01_PRODUCT/decisions.md#d-036) | Пять значений. ПЗ §9 дословно требует «минимум четыре класса», поэтому `UNKNOWN` им разрешён |
| `matched_rule_id` | string | [D-037](../01_PRODUCT/decisions.md#d-037) | Идентификатор сработавшего правила P-0…P-6 или группы. Обязателен: без него неисполним процесс обновления справочника |

**`UNKNOWN` не сериализуется в итоговый JSON** — поля класса ссылки в контракте ПЗ §14 нет вовсе, выходной контракт не меняется.

`IRRELEVANT` присваивается только по положительному признаку и никогда как остаток ([D-036](../01_PRODUCT/decisions.md#d-036)). Полные правила — [link-taxonomy.md](../01_PRODUCT/link-taxonomy.md).

Полей `score` и `reason` для ссылок ПЗ **не предусматривает** — в отличие от документов (§12). Добавлять не следует.

## RelevanceAssessment

Оценка релевантности документа. Источник: ПЗ §12; REQ-016, REQ-017, BR-006.

**Обновлено 2026-08-31** Дополнением к ПЗ §12.1 ([D-042](../01_PRODUCT/decisions.md#d-042)).

| Поле | Тип | Обязательность | Кто заполняет | Источник |
|---|---|---|---|---|
| `relevance_score` | float, `0.0 <= x <= 1.0` | обязательно | **LLM** | Доп. §12.1 |
| `reason` | string | обязательно | **LLM** | Доп. §12.1, ПЗ §12 |
| `relevance` | enum: `HIGH` \| `MEDIUM` \| `LOW` | обязательно | **приложение**, детерминированно из `relevance_score` | Доп. §12.1 |

- Поле `score` из ПЗ §12 переименовано в `relevance_score`. Возвращать `relevance` и число из LLM одновременно **запрещено**.
- Пороги: `>= 0.75 → HIGH`, `>= 0.45 → MEDIUM`, иначе `LOW`. Живут в конфигурации.
- `relevance_score` — **не** калиброванная вероятность.
- Регистр значений enum (`"high"` в примере ПЗ §12 против `HIGH` в Дополнении) остаётся в [OQ-027](../01_PRODUCT/open-questions.md#oq-027).

## Evidence

Фрагмент-доказательство. Источник: ПЗ §13; REQ-018, BR-007, BR-008.

**Схема зафиксирована 2026-08-31** Дополнением к ПЗ §13.5 ([D-044](../01_PRODUCT/decisions.md#d-044)). Единая для внутренней структуры и итогового JSON — сокращённой проекции §14 больше нет.

| Поле | Тип | Обязательность | Источник | Примечание |
|---|---|---|---|---|
| `claim_id` | string | обязательно | Доп. §13.5 | Пример: `claim_001` |
| `claim` | string | обязательно | ПЗ §13, Доп. §13.5 | |
| `source_url` | string | обязательно для DOMAIN CLAIM | ПЗ §13, AC-10, Доп. §13.5 | Конфликт [C-007](../01_PRODUCT/decisions.md#c-007-схема-evidence-13-против-14) **разрешён** в пользу `source_url`; вариант `source` из §14 отменён |
| `document_title` | string | обязательно | Доп. §13.5 | |
| `page` | int | условно | ПЗ §13, AC-11 | Только для PDF; значение для HTML по-прежнему не определено — [OQ-027](../01_PRODUCT/open-questions.md#oq-027) |
| `quote` | string | обязательно | ПЗ §13, Доп. §13.5 | Дословная цитата, не пересказ |
| `support_score` | float, 0..1 | обязательно для evidence, прошедшего verification | Доп. §13.1–13.5 | **Заменяет `confidence`** ([C-010](../01_PRODUCT/decisions.md#c-010-confidence-против-support_score)). Насколько цитата подтверждает claim. Не выводится из `relevance_score` |
| `verification_status` | enum | обязательно | Доп. §13.4, §13.5 | `SUPPORTED` / `WEAK_SUPPORT` / `UNSUPPORTED`; значение `UNRESOLVED` из §13.7 не согласовано — [OQ-030](../01_PRODUCT/open-questions.md#oq-030) |

Поле `confidence` из ПЗ §13 **не используется**.

## ResearchResult

Итоговый результат. Источник: ПЗ §14; REQ-019, REQ-021.

| Поле | Тип | Источник | Примечание |
|---|---|---|---|
| `research_question` | string | ПЗ §14 | |
| `seed_urls` | string[] | ПЗ §14 | |
| `sources_checked` | int | ПЗ §14 | Точная формула подсчёта не задана |
| `documents_found` | int | ПЗ §14 | |
| `relevant_documents` | int | ПЗ §14 | Считаются ли MEDIUM релевантными — не уточнено |
| `sources` | Source[] | ПЗ §14 | `{url, type, status, depth}` |
| `discovered_documents` | DiscoveredDocument[] | ПЗ §14 | `{title, url, type, depth, relevance}` |
| `evidence` | Evidence[] | ПЗ §14 + Доп. §13.5 | Полная форма схемы Evidence, сокращённой проекции больше нет ([D-044](../01_PRODUCT/decisions.md#d-044)) |
| `answer` | string | ПЗ §14 | Итоговый краткий ответ (REQ-021) |
| unresolved-раздел | Claim[] | Доп. §13.4, §13.7 | **Добавлено 2026-08-31.** Claim без достаточного evidence. Имя поля не согласовано: `unresolved_findings` в §13.4 против `unresolved_claims` в §13.7 — [OQ-030](../01_PRODUCT/open-questions.md#oq-030) |

Полная схема с примером — [api-contracts.md](../03_IMPLEMENTATION/api-contracts.md).

### Source (вложенная в ResearchResult)

`{url: string, type: enum(html|pdf), status: enum, depth: int}` — ПЗ §14.

### DiscoveredDocument (вложенная в ResearchResult)

`{title: string, url: string, type: enum(html|pdf), depth: int, relevance: enum}` — ПЗ §14.

Пересечение `Source` и `DiscoveredDocument` с `RawDocument` очевидно, но ПЗ описывает их как отдельные проекции итогового JSON. Объединять их в одну модель без решения не следует ([TQ-02](questions-for-techlead.md#tq-02)).

## CacheEntry

Запись кэша. Источник: ПЗ §20; REQ-025, BR-013.

| Поле | Тип | Источник |
|---|---|---|
| `url` | string | ПЗ §20 |
| `fetch_timestamp` | datetime | ПЗ §20 |
| `status` | enum | ПЗ §20 |
| `content_hash` | string | ПЗ §20 |
| `parsed_text` | string | ПЗ §20 |

ПЗ формулирует этот состав как «желательно сохранять локально» — то есть рекомендация, а не жёсткое требование. Носитель (файлы или SQLite) не выбран — [OQ-014](../01_PRODUCT/open-questions.md#oq-014). Ключ записи, TTL и правила инвалидации не заданы — [OQ-020](../01_PRODUCT/open-questions.md#oq-020), [OQ-025](../01_PRODUCT/open-questions.md#oq-025).

---

## Сводка неопределённостей модели

| Что не определено | Затрагивает | OQ |
|---|---|---|
| Обязательность полей, значения по умолчанию, поведение при отсутствии данных | Все сущности | [OQ-027](../01_PRODUCT/open-questions.md#oq-027) |
| Закрытый перечень `status` для URL | UrlCheckResult, Source | [OQ-024](../01_PRODUCT/open-questions.md#oq-024) |
| Регистр значений enum (`high` против `HIGH`) | RelevanceAssessment, ClassifiedLink | [OQ-027](../01_PRODUCT/open-questions.md#oq-027) |
| Правило вычисления `domain` и `same_domain` | UrlCheckResult, Link | [OQ-013](../01_PRODUCT/open-questions.md#oq-013) |
| Канонизация URL как ключ дедупликации | RawDocument, CacheEntry | [OQ-025](../01_PRODUCT/open-questions.md#oq-025) |
| Перечень `verification_status` и имя unresolved-поля | Evidence, ResearchResult | [OQ-030](../01_PRODUCT/open-questions.md#oq-030) |

**Закрыто 2026-08-31:** именование `source` против `source_url` (C-007 разрешён, [D-044](../01_PRODUCT/decisions.md#d-044)); связь `score` и `relevance` ([D-042](../01_PRODUCT/decisions.md#d-042)); семантика `confidence` — поле заменено на `support_score` ([D-043](../01_PRODUCT/decisions.md#d-043)).

Задача T-002 (схемы Pydantic) остаётся `BLOCKED` до закрытия как минимум OQ-024, OQ-030 и остатка OQ-027.
