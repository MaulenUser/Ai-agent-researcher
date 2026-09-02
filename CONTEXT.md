# Контекст проекта Macroprud

Дата последнего обновления: **2026-09-02**.

Файл описывает, что делается, зачем и в каком состоянии находится код.
Формальные требования — в `source/постановка задач.md` и `docs2/`.

## 1. Зачем проект

Аналитику по макропруденциальному регулированию (CCyB, SyRB, D-SIB/O-SII, буфер
консервации, LTV/DSTI/DTI, LCR/NSFR) нужно находить первоисточники на сайтах
регуляторов. Вручную это обход десятков сайтов: нужный документ обычно лежит не
на стартовой странице, а на 1–2 уровня глубже, часто в PDF.

Система принимает исследовательский вопрос и стартовые URL и проходит цепочку:

```
URL → Page → Links → Documents → Text → Relevant Evidence
```

Результат — JSON + Markdown-отчёт, где каждый факт снабжён ссылкой на источник
(для PDF — с номером страницы).

Цель первого этапа (ПЗ §26): доказать, что система доходит от стартовой страницы
до вложенного первоисточника и извлекает из него evidence. Домен важен как
источник тестовых данных, сам конвейер предметно-нейтрален.

## 2. Что уже работает

Каталог `regulatory-research-agent/`. Реализованный пайплайн:

```
URL → HTTP 200 → HTML → основной текст
    → extract_links() → normalize URL → deduplicate
    → taxonomy classification → P-3 navigation filtering → candidate links
```

| Файл | Назначение |
|---|---|
| `app/fetcher.py` | Загрузка по URL, httpx + async, редиректы |
| `app/html_parser.py` | title, заголовки, основной текст (trafilatura) |
| `app/link_extractor.py` | Абсолютные ссылки, нормализация URL, дедупликация, DOM-контекст (`in_nav`, ближайший заголовок) |
| `app/taxonomy.py` | Классификация ссылок, `matches_keyword`, фильтр навигации |
| `config/link_taxonomy.yaml` | Все правила классификации. Кода в правилах нет |
| `app/main.py` | Точка входа, URL задан константой |

Классы ссылок: `HIGH_VALUE`, `POTENTIALLY_RELEVANT`, `NAVIGATION`, `IRRELEVANT`,
`OTHER`. Кандидаты на обход — первые два. Каждая ссылка получает `reason` —
строку с причиной решения; она нужна для отладки crawler'а («почему этот
документ не открыли»).

## 3. Проверенный результат

Прогон 2026-09-01 на `https://www.mnb.hu/en/financial-stability/macroprudential-policy/the-macroprudential-toolkit/countercyclical-capital-buffer-ccyb`
(источник URL — `source/links.md`, строка 13):

```
HTTP 200 → 158 ссылок → 31 candidate
HIGH_VALUE 15 | POTENTIALLY_RELEVANT 16 | NAVIGATION 67 | IRRELEVANT 42 | OTHER 18
```

Найдены и сохранены: 3 PDF с методологией CCyB, 7 PDF с обоснованиями решений,
8 press releases, `Previous decisions, justifications and systemic risk maps`,
`Related links`, `Research papers`, `Archive`, xlsx с данными.
Отфильтрованы: `Cookie Guidelines`, `Contact Us`, `Careers`, `Museum`,
`Payment Systems Report`, `Publications` в меню.

Тесты: `py -3.10 -m pytest -q` → **48 passed** (перепроверено 2026-09-02).

`python -m pytest -q` **падает**: `ModuleNotFoundError: No module named 'yaml'`.
`.venv/` в корне — Python 3.14.2 без зависимостей и при этом интерпретатор по
умолчанию; зависимости стоят в глобальном 3.10. Окружение подлежит починке.

## 4. Источник правил классификации

`config/link_taxonomy.yaml` собран из `docs2/01_PRODUCT/link-taxonomy.md`:

| Правило в коде | Источник |
|---|---|
| Группы и ключевые слова | §4, строки 97–110 |
| `ignore_extensions` (P-0) | §5, строка 130 |
| `unrelated_topic` (P-2) | §5, строка 136 + §4, строка 110 |
| `foreign_domains` (P-5) | §5, строка 164 |
| `potentially_relevant.section_anchors` | §5, строка 152 |
| Документ не понижается до `NAVIGATION` | §6.1, строка 195 |
| Путь к конфигу | §10, строка 266 |

Совпадение — по границам токенов (`matches_keyword`), не по подстроке:
`resolution` матчит `/resolution/` и `resolution-of-the-board`, но не `irresolution`;
`report` не матчит `reporting`. Множественное число учитывается.

## 5. Решения, принятые без БА

**Заведены как OQ 2026-09-02:** [OQ-031](docs2/01_PRODUCT/open-questions.md#oq-031), [OQ-032](docs2/01_PRODUCT/open-questions.md#oq-032), [OQ-033](docs2/01_PRODUCT/open-questions.md#oq-033), [OQ-034](docs2/01_PRODUCT/open-questions.md#oq-034) — по одному на каждый пункт ниже. Пятое, `same_domain`, попадает в уже открытый [OQ-013](docs2/01_PRODUCT/open-questions.md#oq-013). До ответов считать их временными; расширять эти участки нельзя.

1. **`Cookie Guidelines` → `NAVIGATION`.** Подстрока `guideline` из `high_value`
   сработала бы раньше навигации. Введено исключение: точное совпадение anchor
   со списком `navigation.anchors` отменяет правило 1.
2. **PDF без тематического признака → `POTENTIALLY_RELEVANT`**, не `HIGH_VALUE`
   и не `OTHER`. Причина: `ccyb-indoklas-2026q2-en.pdf` — обоснование решения,
   но слово венгерское и в списках его нет; документ не должен теряться.
3. **`Related links` в `<nav>` остаётся кандидатом.** По P-3 (`link-taxonomy.md`
   строка 152) группа `related_material` в меню должна была бы стать
   `NAVIGATION`; сохранение related documents было прямым требованием.
4. **`topic_match` считается лексически из `<title>` страницы.** Заглушка до
   появления research question и LLM, не бизнес-правило.

## 6. Границы: чего в коде нет

Не реализовано и намеренно не начиналось: LLM-оценка релевантности, извлечение
текста из PDF, рекурсивный обход глубже стартовой страницы, JSON/Markdown-отчёт,
CLI-аргументы, логирование, кэш, тестовый датасет по нескольким регуляторам.

Не входит в MVP по ПЗ §4: JS-браузер, CAPTCHA, авторизация, OCR, DOCX/XLSX по
содержимому, граф знаний, vector DB, scheduled monitoring, production-UI.

## 7. Особенности среды

- Python 3.10.0 на машине разработчика — ниже требуемого ПЗ 3.11+ (`OQ-019`).
- Корпоративный TLS-proxy подменяет сертификаты. Решение: `truststore.SSLContext`
  в `app/fetcher.py` (берёт корни из хранилища Windows). Проверка сертификата не
  отключена. Для `pip` нужны `--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
- Консоль Windows по умолчанию cp1251 и падает на венгерских буквах —
  в `app/main.py` стоит `sys.stdout.reconfigure(encoding="utf-8")`.
- Старой версии `trafilatura` под 3.10 нужен отдельный пакет `lxml_html_clean`.

## 8. Сверка с docs2 — выполнена 2026-09-02

Код писался по `link-taxonomy.md` и прямым указаниям в сессии; `open-questions.md`,
`status.md`, `tasks.md`, `business-rules.md`, `decisions.md`, `business-requirements.md`
при этом не открывались. 2026-09-01 из `CLAUDE.md` было удалено требование читать
`docs2/` перед изменением кода.

Сверка проведена 2026-09-02. Найдено 11 расхождений кода с документацией и 5 решений,
принятых вместо БА. Полный перечень с привязкой к строкам —
[docs2/03_IMPLEMENTATION/status.md](docs2/03_IMPLEMENTATION/status.md), разделы
«Расхождения кода с документацией» и «Решения, принятые разработчиком вместо БА».
Статусы задач и GAP приведены в соответствие с фактическим кодом.

Этот файл (`CONTEXT.md`) описывает **что и как работает**. Источник статуса —
`status.md`; при расхождении верен он.

## 9. Запуск

```bash
cd regulatory-research-agent
py -3.10 -m pytest -q        # 48 passed
py -3.10 -m app.main         # URL задан в app/main.py
```

`python` без указания версии сейчас разрешается в пустой `.venv` (3.14.2) и падает.
Правильная починка — создать venv на поддерживаемой версии и установить в него
`requirements.txt` (нужны `--trusted-host pypi.org --trusted-host files.pythonhosted.org`
из-за корпоративного TLS-proxy). Какая версия допустима — [OQ-019](docs2/01_PRODUCT/open-questions.md#oq-019).

**Прогон `app.main` ходит на сайты регуляторов без robots.txt, задержек и
предписанного User-Agent** (BR-016, BR-017 не реализованы). До приведения
`fetcher.py` в соответствие реальные прогоны не проводить.
