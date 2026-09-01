# Контракты

**Дата среза:** 2026-08-31.

> **AS IS: контрактов не существует.** HTTP API у системы нет и не предусмотрено — ПЗ описывает только CLI (§27, D-019). Ни один модуль не реализован, ни одна схема не объявлена.
>
> Ниже — целевые контракты, восстановленные из примеров JSON в ПЗ. **ПЗ приводит примеры, а не схемы**: типы, обязательность и допустимые значения в нём почти не заданы. Незакрытые места помечены и не заполняются самостоятельно.

## Виды контрактов в проекте

| Вид | Есть в ПЗ | Статус |
|---|---|---|
| CLI-контракт | §27 | Частично определён, формат входного файла открыт |
| Контракт выходного JSON | §14 | Определён на уровне примера |
| Контракт Markdown-отчёта | §15 | Определён на уровне примера |
| Внутренние контракты между модулями | §6–§13 | Определены на уровне примеров |
| HTTP API системы | — | **Не предусмотрен ПЗ.** Раздел неприменим |
| Контракт LLM API | — | **Не определён.** Провайдер выбран 2026-08-31 ([D-031](../01_PRODUCT/decisions.md#d-031)); промпты, схемы ответа и модель под задачу — нет ([OQ-028](../01_PRODUCT/open-questions.md#oq-028)) |

---

## 1. CLI-контракт

**Источник:** ПЗ §27. Требования: REQ-022, REQ-023.

```bash
python -m app.main \
  --question "Does the regulator use a positive-neutral CCyB?" \
  --urls urls.json
```

| Аргумент | Обязательность | Описание | Источник |
|---|---|---|---|
| `--question` | обязателен | Исследовательский вопрос (REQ-001) | ПЗ §27 |
| `--urls` | обязателен | Путь к файлу со списком seed URL | ПЗ §27 |

**Выход:**

```
data/results/research_result.json
data/results/research_report.md
```

**Не определено:**

- формат файла `urls.json` — [OQ-015](../01_PRODUCT/open-questions.md#oq-015). ПЗ §3 показывает единый объект `{research_question, seed_urls}`, ПЗ §27 — раздельную передачу. Согласование обязательно до T-004;
- коды возврата процесса; ПЗ не описывает;
- дополнительные аргументы (путь вывода, уровень логирования, лимиты) — в ПЗ отсутствуют, добавлять без решения не следует.

## 2. Выходной JSON

**Источник:** ПЗ §14. Требование: REQ-019. Приёмка: AC-12.

```json
{
  "research_question": "...",
  "seed_urls": [],
  "sources_checked": 18,
  "documents_found": 11,
  "relevant_documents": 5,
  "sources": [
    { "url": "...", "type": "html", "status": "accessible", "depth": 0 }
  ],
  "discovered_documents": [
    { "title": "...", "url": "...", "type": "pdf", "depth": 1, "relevance": "high" }
  ],
  "evidence": [
    { "claim": "...", "quote": "...", "source": "...", "page": 9 }
  ],
  "answer": "..."
}
```

| Поле | Тип | Обязательность | Примечание |
|---|---|---|---|
| `research_question` | string | не задана | Эхо входного вопроса |
| `seed_urls` | string[] | не задана | Эхо входных URL |
| `sources_checked` | int | не задана | Формула подсчёта не определена |
| `documents_found` | int | не задана | — |
| `relevant_documents` | int | не задана | Входят ли MEDIUM — не определено |
| `sources[]` | object[] | не задана | `{url, type, status, depth}` |
| `discovered_documents[]` | object[] | не задана | `{title, url, type, depth, relevance}` |
| `evidence[]` | object[] | не задана | **Единая схема Доп. §13.5** — см. ниже. Сокращённой формы §14 больше нет |
| `answer` | string | не задана | Итоговый краткий ответ (REQ-021) |
| unresolved-раздел | object[] | не задана | **Добавлено Доп. §13.4, §13.7.** Имя поля не согласовано: `unresolved_findings` против `unresolved_claims` — [OQ-030](../01_PRODUCT/open-questions.md#oq-030) |

**Конфликт разрешён 2026-08-31.** Дополнение к ПЗ §13.5 вводит единую схему и дословно фиксирует: «ошибка первоначального §14 устраняется». Действующая схема ([D-044](../01_PRODUCT/decisions.md#d-044)):

```json
{
  "claim_id": "claim_001",
  "claim": "The CNB uses a positive-neutral CCyB framework.",
  "source_url": "https://...",
  "document_title": "The CNB's approach...",
  "page": 9,
  "quote": "...",
  "support_score": 0.96,
  "verification_status": "SUPPORTED"
}
```

Историческая справка о конфликте — [C-007](../01_PRODUCT/decisions.md#c-007-схема-evidence-13-против-14). Отменены: имя `source` из §14, поле `confidence` из §13, сокращённая проекция evidence в итоговом JSON.

**Что в схеме evidence всё ещё не закрыто:** перечень значений `verification_status` ([OQ-030](../01_PRODUCT/open-questions.md#oq-030)) и значение `page` для HTML-источника ([OQ-027](../01_PRODUCT/open-questions.md#oq-027)).

**Прочие незакрытые места контракта:**

| Что | OQ |
|---|---|
| Перечень допустимых значений `status` в `sources[]` | [OQ-024](../01_PRODUCT/open-questions.md#oq-024) |
| Регистр значений `relevance`: `"high"` (пример §14) против `HIGH` (перечень §12) | [OQ-027](../01_PRODUCT/open-questions.md#oq-027) |
| Значение `page` для evidence из HTML | [OQ-027](../01_PRODUCT/open-questions.md#oq-027) |
| Обязательность полей и представление отсутствующих значений | [OQ-027](../01_PRODUCT/open-questions.md#oq-027) |
| Попадают ли в `discovered_documents[]` документы со статусом `ocr_required` и недоступные | [OQ-027](../01_PRODUCT/open-questions.md#oq-027) |
| Отражается ли усечение результата по лимиту (BR-003) | Продуктовое решение, см. [workflow.md, S-05](../01_PRODUCT/workflow.md#сценарий-s-05-достижение-лимита-обхода) |

## 3. Markdown-отчёт

**Источник:** ПЗ §15. Требование: REQ-020. Приёмка: AC-13.

Структура из ПЗ:

```markdown
# Research Result

## Seed URL 1
Status: Accessible

### Relevant documents found

1. Methodological framework
2. Decision 2025 Q4
3. Financial Stability Report

### Findings

- Positive-neutral CCyB is explicitly mentioned.
- Neutral rate: 1%.
- Transition began in 2024.

### Evidence

> "..."

Source: ...
Page: ...
```

Обязательные элементы: заголовок отчёта; секция на каждый seed URL с его статусом; список найденных релевантных документов; findings; evidence в виде цитаты с указанием источника и страницы (BR-007, BR-008).

**Не определено:** язык отчёта ([OQ-011](../01_PRODUCT/open-questions.md#oq-011)); отображается ли итоговый `answer` в отчёте (в примере §15 его нет, хотя в JSON он есть); как показывать недоступные seed URL; что писать в `Page:` для HTML-источника.

## 4. Внутренние контракты между модулями

Структуры перечислены в [domain-model.md](../02_TECHNICAL/domain-model.md) с указанием источника каждого поля. Здесь — только соответствие «стадия → выход», по ПЗ §5.

| Стадия | Вход | Выход | Источник структуры |
|---|---|---|---|
| URL Validator | seed URL | `UrlCheckResult` | ПЗ §6 |
| Page Fetcher | `UrlCheckResult` | `RawDocument` | Выведена, PROPOSAL — [TQ-02](../02_TECHNICAL/questions-for-techlead.md#tq-02) |
| Content Parser (HTML) | `RawDocument` | `ParsedPage` | ПЗ §7 |
| Content Parser (PDF) | `RawDocument` | `ParsedPdf` | ПЗ §11 |
| Link Extractor | `ParsedPage` | `Link[]` | ПЗ §8 |
| Link Classifier | `Link[]` | `ClassifiedLink[]` | ПЗ §9 |
| Crawler | `ClassifiedLink[]` | новые `RawDocument` на depth+1 | ПЗ §10 |
| Relevance Analysis | `ParsedPage` / `ParsedPdf` | `RelevanceAssessment` | ПЗ §12 |
| Evidence Extraction | документы HIGH/MEDIUM | `Evidence[]` | ПЗ §13 |
| Synthesizer | `Evidence[]` | `answer` + отчёт | ПЗ §14, §15 |

Примеры JSON для каждой структуры приведены в ПЗ §6–§14 и должны использоваться как тест-кейсы валидации схем (T-002).

## 5. Контракт LLM API

Определён частично. Известны с 2026-08-31:

- Провайдер и доступ: OpenAI-совместимый шлюз `https://prod-litellm.nationalbank.kz/v1`, ключ из `.env`, пул из трёх моделей Qwen ([D-031](../01_PRODUCT/decisions.md#d-031)).
- **Контракт оценки релевантности** ([D-042](../01_PRODUCT/decisions.md#d-042)): LLM возвращает `{relevance_score: float 0..1, reason: string}` — и ничего больше. Класс вычисляет приложение по порогам 0.75 / 0.45 из конфигурации.
- **Контракт evidence** ([D-043](../01_PRODUCT/decisions.md#d-043), [D-044](../01_PRODUCT/decisions.md#d-044)): два вызова. Extraction → `{claim, quote, source_url, page}`. Verification (отдельный prompt, `temperature = 0`, без reasoning шага A) → `{support_score, verification_reason, status}`. Пороги 0.80 / 0.60.

Не заданы: модель под каждую задачу ([OQ-028](../01_PRODUCT/open-questions.md#oq-028)), тексты промптов, перечень значений `verification_status` ([OQ-030](../01_PRODUCT/open-questions.md#oq-030)), поведение при отказе ([OQ-006](../01_PRODUCT/open-questions.md#oq-006)), стратегия для длинных документов ([TQ-03](../02_TECHNICAL/questions-for-techlead.md#tq-03)).

Единственное фиксируемое сейчас требование — доступ к LLM изолирован за одним внутренним интерфейсом (REQ-028, «единый LLM API»). Подробнее — [integrations.md, INT-02](../02_TECHNICAL/integrations.md#int-02-llm-api).

## 6. HTTP API системы

**Раздел неприменим.** ПЗ не предусматривает у системы серверного API: единственный интерфейс этапа 1 — CLI (§27), production-UI исключён из объёма (§4).

Раздел понадобится, если появится требование запускать исследования удалённо или встраивать систему в другой сервис — то есть на этапе «production research platform» из ПЗ §28. До этого проектировать HTTP API не следует: это выход за границы MVP (D-002).
