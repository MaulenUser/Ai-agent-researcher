# Regulatory Research Agent

Каркас MVP. Документация проекта — [../docs2/README.md](../docs2/README.md).

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python -m app.main
```

URL задан в `app/main.py`. Пайплайн:

```
HTML → extract_links() → normalize URL → deduplicate
     → taxonomy classification → P-3 navigation filtering → candidate links
```

Порядок правил (`app/taxonomy.py`, правила — в YAML):

| # | Правило | Класс |
|---|---|---|
| P-0 | картинки, стили, скрипты | не классифицируется |
| P-2 / P-5 | чужая тема (museum, career) и чужая политика регулятора (payment systems) | `IRRELEVANT` |
| 1 | anchor из `high_value` | `HIGH_VALUE` |
| 2 | тип документа в URL (+ расширение) | `HIGH_VALUE` |
| 3 | расширение `.pdf/.xlsx/.docx` без тематики | `POTENTIALLY_RELEVANT` |
| 4 | anchor из `potentially_relevant` | `POTENTIALLY_RELEVANT` |
| 5 | навигация, P-3 | `NAVIGATION` |
| 6 | остальное | `OTHER` |

Тема (`topic_match`) считается лексически из `<title>` страницы — до подключения LLM.
Документ (pdf/xlsx/docx) не понижается до `NAVIGATION`, даже находясь в меню.

Вывод в консоль: HTTP-статус, content-type, title, заголовки, основной текст,
разбивка ссылок по классам и список кандидатов с `class` + `reason`.

Классы: `HIGH_VALUE`, `POTENTIALLY_RELEVANT`, `NAVIGATION`, `IRRELEVANT`, `OTHER`.
Кандидаты — первые два, остальные печатаются в блоке `FILTERED OUT`. `reason` объясняет, почему ссылка попала в класс
(нужен при отладке crawler'а: «почему этот документ не открыли»).

## Тесты

```bash
pytest
```

## Структура

| Путь | Назначение |
|---|---|
| `app/fetcher.py` | HTTP-загрузка по URL (httpx, async) |
| `app/html_parser.py` | title, заголовки, основной текст (trafilatura) |
| `app/link_extractor.py` | Ссылки: нормализация URL, дедупликация, контекст |
| `app/taxonomy.py` | Классификация по 6 правилам + фильтр навигации |
| `config/link_taxonomy.yaml` | Правила классификации (без кода) |
| `app/main.py` | Точка входа |
| `data/results/` | Выходные файлы (пока не используются) |
