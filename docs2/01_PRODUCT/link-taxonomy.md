# Таксономия и классификация ссылок — формальная спецификация v1

**Дата:** 2026-08-31. **Версия спецификации:** 1.0.0. **Статус:** CONFIRMED.

**Основание.** Письменный ответ БА от 2026-08-31 на [OQ-002](open-questions.md#oq-002) и [OQ-012](open-questions.md#oq-012). БА потребовал формальную спецификацию вместо открытых перечней и **назначил владельцем таксономии разработчика / project maintainer** (п. 8 ответа). Поэтому содержание правил ниже — не самостоятельное «придумывание бизнес-логики», а исполнение делегированного БА полномочия. Решения — [D-035…D-040](decisions.md).

**Что этот документ НЕ определяет** (осталось за БА, [OQ-029](open-questions.md#oq-029)): по каким классам crawler переходит на следующий уровень глубины и что делать с `UNKNOWN` в MVP. Классификация и политика обхода — разные решения; T-009 отвечает только за первое.

**Реализация:** T-009. **Хранилище правил:** `config/link_taxonomy.yaml` (см. §9). **Проверка:** evaluation dataset (см. §12).

---

## 0. Модель в двух слоях

ПЗ §9 задаёт четыре класса, но не даёт правил отнесения. Прямое отображение «строка anchor text → класс» отвергнуто ответом БА (п. 6: «Классификация не должна основываться только на точном совпадении anchor text»). Принята двухслойная схема (п. 7 ответа):

```
признаки ссылки  →  семантическая группа  →  итоговый класс
(11 фич)            (12 групп)              (4 класса + UNKNOWN)
```

Смысл разделения: группа отвечает на вопрос «**что это за документ**», `research_question` — на вопрос «**про то ли это**». Класс — функция обоих. Поэтому одна и та же ссылка на `methodology.pdf` может быть `HIGH_VALUE` для одного исследовательского вопроса и `POTENTIALLY_RELEVANT` для другого, и это корректное поведение, а не ошибка.

## 1. Итоговые классы

| Класс | Назначение | Определяется |
|---|---|---|
| `HIGH_VALUE` | Ссылка ведёт на документ того типа, который способен содержать прямой ответ, и тематически связан с `research_question` | положительно |
| `POTENTIALLY_RELEVANT` | Ссылка ведёт на документ или раздел правильной предметной области, но либо тип документа вторичен, либо тематическая связь косвенная | положительно |
| `NAVIGATION` | Служебная ссылка структуры сайта, не несущая содержания | положительно |
| `IRRELEVANT` | Ссылка ведёт на **явно иную** тему | положительно, **не остаток** |
| `UNKNOWN` | Внутренний класс: признаков недостаточно для уверенного отнесения | остаток |

**Ответ на главный вопрос ответа БА (п. 3, п. 14): `IRRELEVANT` — самостоятельный положительно определяемый класс.** Он присваивается только при наличии явного признака нерелевантности (§5, группа `unrelated_topic`). Ссылка, о которой ничего не известно, `IRRELEVANT` **не получает** — она получает `UNKNOWN`.

**Ответ на п. 4: `UNKNOWN` нужен.** Три причины: (1) без него `IRRELEVANT` неизбежно вырождается в остаток, что ответ БА запрещает; (2) он даёт измеримую метрику качества таксономии — доля `UNKNOWN` на evaluation dataset; (3) он формирует очередь кандидатов для процесса обновления справочника (§10) и для возможного LLM-доклассификатора (ПЗ §18), если тот будет утверждён.

**Совместимость с ПЗ.** ПЗ §9 дословно: «Система должна разделить ссылки **минимум** на четыре класса». Слово «минимум» прямо разрешает пятое значение — конфликта нет. Прежняя формулировка docs2 «ровно на четыре класса» ([D-014](decisions.md)) была ужесточением ПЗ и переведена в `SUPERSEDED`.

**Область видимости `UNKNOWN`.** Класс внутренний. В итоговый JSON он не попадает, потому что `link_class` в выходной контракт ПЗ §14 не входит вовсе (`sources[]` и `discovered_documents[]` полей класса ссылки не содержат). Выходной контракт не меняется.

## 2. Признаки (features)

Классификатор обязан принимать на вход минимум эти 11 признаков (п. 6 ответа БА). Ни один из них не является единственным основанием для решения.

| # | Признак | Источник | Примечание |
|---|---|---|---|
| F-01 | `research_question` | `ResearchRequest` (ПЗ §3) | Нормализуется, см. §3 |
| F-02 | `anchor_text` | `Link` (ПЗ §8) | Может быть пустым (ссылка-картинка) |
| F-03 | `target_url` | `Link` (ПЗ §8) | Абсолютный, после нормализации T-005 |
| F-04 | URL path | производный от F-03 | Сегменты пути в нижнем регистре |
| F-05 | file extension / MIME type | `Link.extension` (ПЗ §8) | MIME известен только после загрузки — на этапе классификации используется расширение |
| F-06 | `surrounding_text` | **новое поле**, см. §2.1 | Текст ближайшего блочного контейнера |
| F-07 | `section_heading` | **новое поле**, см. §2.1 | Ближайший предшествующий h1–h6 |
| F-08 | DOM position / context | **новое поле**, см. §2.1 | Имя ближайшего семантического контейнера |
| F-09 | `source_page_topic` | производный | `title` + h1 страницы-источника (`ParsedPage`, ПЗ §7) |
| F-10 | `same_domain` | `Link` (ПЗ §8) | Правило вычисления — [OQ-013](open-questions.md#oq-013), таксономия его не определяет |
| F-11 | authority of external source | `config/link_taxonomy.yaml` | Три корзины, см. §5.4 |

### 2.1. Следствие: модель `Link` расширяется

Признаки F-06, F-07, F-08 в ПЗ §8 отсутствуют — там пять полей. Ответ БА (п. 6) делает их обязательными, поэтому `Link` дополняется вложенной структурой `context`:

```
Link.context = {
  surrounding_text: string,   # текст родительского блока, обрезанный до N символов
  section_heading:  string,   # ближайший предшествующий заголовок h1–h6
  dom_container:    string    # nav | header | footer | main | aside | table | list | body
}
```

Это **расширение**, а не противоречие: ПЗ §8 приводит пример JSON, а не закрытую схему, и `Link` в выходной контракт §14 не входит. Зафиксировано как [D-039](decisions.md). Практическое следствие: **объём T-008 увеличивается** — извлечение ссылок обязано заполнять `context`. T-008 остаётся `BLOCKED` по своей причине ([OQ-013](open-questions.md#oq-013)), но её критерии готовности дополнены.

## 3. Обработка `research_question` (п. 2 ответа: «зависимость классификации от research_question»)

Детерминированная, без LLM — иначе нарушается ПЗ §18 («детерминированные задачи не отдавать LLM»).

1. Нормализация: нижний регистр, удаление пунктуации, токенизация по пробелам.
2. Удаление стоп-слов по списку `stopwords` из справочника.
3. Расширение синонимами: каждый токен и каждая биграмма ищутся в разделе `synonyms` справочника; найденное добавляется в множество терминов вопроса `Q`.
4. Формируется `V` — общая предметная лексика (раздел `domain_vocabulary`), не зависящая от вопроса.

`topic_match` вычисляется по конкатенации `anchor_text + URL path + section_heading`:

| Значение | Условие |
|---|---|
| `direct` | найден хотя бы один термин из `Q` |
| `partial` | термин из `Q` не найден, но найден термин из `V` |
| `none` | не найдено ничего |

Пример из ПЗ §12 работает именно так: вопрос про «positive neutral rate» через `synonyms` расширяется до `standard CCyB rate`, и ссылка с anchor `Standard CCyB rate` получает `topic_match = direct`. Требование семантической эквивалентности (REQ-017) на уровне **ссылок** закрывается словарём синонимов; на уровне **документов** оно остаётся за LLM (T-012) — там оно и сформулировано в ПЗ §12.

## 4. Семантические группы

Группы приняты по п. 7 ответа БА и дополнены `topic_landing` — без неё примеры ПЗ §9 `financial stability`, `macroprudential policy`, `capital buffers` не отображались бы ни в одну группу.

| Группа | Ранг | Назначение | Сильные признаки | Слабые признаки |
|---|---|---|---|---|
| `regulatory_decision` | primary | Решение регулятора, правовой акт | anchor: decision, provision, regulation, resolution, legal act, measure; URL: `/decision`, `/legal`, `/regulation` | anchor: notice, announcement |
| `methodology` | primary | Как считается показатель | anchor: methodology, methodological framework, technical note, framework, annex; URL: `/methodolog`, `/framework` | anchor: approach, note, explanatory |
| `official_information` | primary | Официальная позиция и коммуникация | anchor: official information, press release, opinion, statement, guidelines, recommendation; URL: `/press`, `/opinion`, `/guidelines` | anchor: news, communication |
| `financial_report` | primary | Регулярные отчёты | anchor: financial stability report, macroprudential report, annual report, review; URL: `/fsr`, `/report` | anchor: report, bulletin |
| `consultation` | primary | Консультации и обсуждения | anchor: consultation, consultation paper, call for advice; URL: `/consultation` | anchor: feedback, comments |
| `research` | primary | Исследовательские материалы | anchor: research paper, working paper, occasional paper, study; URL: `/research`, `/working-paper` | anchor: paper, analysis |
| `data` | secondary | Числовые данные и таблицы | anchor: data, statistics, time series, rates, indicators; расширение `xlsx`, `csv`; URL: `/statistics`, `/data` | anchor: figures, table |
| `archive` | secondary | Исторические версии | anchor: archive, previous decisions, past releases, history; URL: `/archive`, `/history` | anchor: previous, earlier |
| `topic_landing` | secondary | Раздел предметной области | anchor: financial stability, macroprudential policy, capital buffers, systemic risk; URL: `/financial-stability`, `/macroprudential` | anchor совпадает с термином из `V` |
| `related_material` | secondary | Отсылка к смежным материалам | anchor: related documents, related publications, publications, see also, further reading | anchor: more information, links |
| `navigation` | navigation | Служебная структура сайта | anchor: home, contact, about, careers, language, privacy, sitemap, search, login, terms, accessibility, cookies, rss, subscribe | — |
| `unrelated_topic` | unrelated | Явно иная тема | anchor/URL: museum, exhibition, visitor centre, tours, numismatics, coins, banknote gallery, sponsorship, sport, art collection, procurement, tenders; чужая предметная область (см. §5.5) | — |

**Это не закрытый словарь строк** (п. 11 ответа БА). Перечни выше — стартовое наполнение `config/link_taxonomy.yaml` версии 1.0.0. Сопоставление ведётся по нормализованной подстроке и по регулярным выражениям из справочника, а не по точному равенству; справочник пополняется процессом §10.

**Детерминированный tie-break.** Если ссылка попадает более чем в одну группу с одинаковой силой признака, выигрывает группа выше в порядке:

```
regulatory_decision > methodology > official_information > financial_report >
consultation > research > data > archive > topic_landing > related_material >
navigation > unrelated_topic
```

Сильный признак всегда побеждает слабый независимо от порядка.

## 5. Порядок применения правил (п. 5 ответа БА)

Правила применяются строго по порядку. Первое сработавшее завершает классификацию.

### P-0. Предфильтр — ссылка не классифицируется вовсе

Схема не `http`/`https` (BR-010), `mailto:`, `tel:`, `javascript:`, ссылка-якорь на ту же страницу (`#...`), расширение из списка `extensions.ignore` (`jpg`, `png`, `svg`, `css`, `js`, `ico`, `woff`). Такие ссылки не получают класса и не попадают в `ClassifiedLink`.

### P-1. Исключённый внешний домен → `IRRELEVANT`

`same_domain = false` и домен в корзине `domain_authority.excluded` (соцсети, видеохостинги, CDN, аналитика). Это положительный признак нерелевантности, а не остаток.

### P-2. Признак чужой темы в URL path побеждает anchor text → `IRRELEVANT`

Если URL path содержит признак `unrelated_topic`, ссылка получает `IRRELEVANT` **даже если anchor text попадает в primary-группу**.

Это прямой ответ на случай 1 ответа БА: `anchor = "Methodology"`, ссылка ведёт на музей центрального банка → `IRRELEVANT`. Обоснование: путь URL отражает раздел сайта и надёжнее текста ссылки, который может быть переиспользован шаблоном.

**Исключение:** если в URL path одновременно присутствует термин из `Q` (`topic_match = direct` по признаку URL), сигналы противоречат друг другу → `UNKNOWN` и запись в лог, а не молчаливый выбор.

### P-3. Служебная навигация → `NAVIGATION`

Срабатывает при одновременном выполнении:
- `dom_container` ∈ {`nav`, `header`, `footer`} (или элемент внутри `[role=navigation]`, breadcrumbs);
- группа ∈ {`navigation`, `related_material`, отсутствует};
- `topic_match` ≠ `direct`;
- расширение не `pdf` (ссылка на документ не является навигацией, даже находясь в подвале).

Это ответ на случаи 3 и 4 ответа БА: `Publications` в основном меню → `NAVIGATION`; `Related publications` внутри контента страницы CCyB → правило не срабатывает (`dom_container = main`), ссылка уходит в матрицу §6 и получает `POTENTIALLY_RELEVANT`.

Группы `primary` через это правило **не проходят** намеренно: `Financial Stability Report` в верхнем меню остаётся содержательной ссылкой.

### P-4. Разрешение обобщённого anchor text по контексту

Если `anchor_text` входит в список `generic_anchors` (`download`, `read more`, `more`, `here`, `click here`, `link`, `pdf`, `open`, `view`) либо пуст, то группа и `topic_match` вычисляются **не по anchor text**, а по `section_heading`, затем `surrounding_text`, затем URL path.

Это ответ на случай 2 ответа БА: `anchor = "Download"` под заголовком `Countercyclical capital buffer methodology` → группа `methodology`, `topic_match = direct` → `HIGH_VALUE`.

Если ни заголовок, ни окружающий текст, ни URL не дают группы → `UNKNOWN`.

### P-5. Чужая предметная область → `IRRELEVANT`

Anchor или URL относятся к явно названной иной политике или функции регулятора (`monetary policy`, `payment systems`, `banknotes and coins`, `foreign exchange reserves`, `deposit insurance`), и при этом `topic_match ≠ direct`.

Зависимость от вопроса обязательна: если `research_question` касается денежно-кредитной политики, `monetary policy` даёт `topic_match = direct`, правило не срабатывает, и ссылка классифицируется по матрице §6 как содержательная. Список `foreign_domains` в справочнике задаёт предметные области, чужие для макропруденциального контура.

### P-6. Матрица §6

Все остальные случаи.

## 6. Матрица «ранг группы × тематическое совпадение»

| Ранг группы \ `topic_match` | `direct` | `partial` | `none` |
|---|---|---|---|
| **primary** | `HIGH_VALUE` | `HIGH_VALUE` | `POTENTIALLY_RELEVANT` |
| **secondary** | `HIGH_VALUE` | `POTENTIALLY_RELEVANT` | `POTENTIALLY_RELEVANT` |
| **navigation** | `POTENTIALLY_RELEVANT` | `NAVIGATION` | `NAVIGATION` |
| **unrelated** | `UNKNOWN` | `IRRELEVANT` | `IRRELEVANT` |
| **группа не определена** | `POTENTIALLY_RELEVANT` | `POTENTIALLY_RELEVANT` | `UNKNOWN` |

Обоснование двух неочевидных клеток:

- **primary + partial → `HIGH_VALUE`.** Документ нужного типа в нужной предметной области ценен, даже если формулировка вопроса в нём не повторяется дословно; окончательное решение всё равно принимает семантическая оценка документа (T-012, ПЗ §12). Ошибка в эту сторону стоит одного лишнего документа из бюджета в 50, ошибка в обратную — пропуска первоисточника, то есть провала AC-09.
- **unrelated + direct → `UNKNOWN`.** Признаки противоречат друг другу; выбор любого из них был бы догадкой.

Клетка «unrelated + partial/none → `IRRELEVANT`» — единственный путь к `IRRELEVANT` кроме P-1, P-2 и P-5. Все они требуют **положительного** признака.

### 6.1. Влияние расширения файла (п. 2 ответа БА)

| Расширение | Действие |
|---|---|
| `pdf` | Усиливает признак документа: слабый признак группы повышается до сильного; блокирует P-3 (`NAVIGATION`) |
| `xlsx`, `xls`, `csv` | Принудительно назначает группу `data` (rank secondary), если более сильная группа не найдена |
| `zip`, `7z` | Группа `data`, сила признака — слабая |
| `doc`, `docx`, `pptx` | Признак документа, как `pdf`, но вне объёма MVP по содержимому (ПЗ §4) |
| отсутствует / `html`, `htm`, `aspx`, `php` | Нейтрально, на классификацию не влияет |
| из списка `ignore` | P-0, ссылка не классифицируется |

**Граница ответственности.** Классификатор не решает, можно ли файл загрузить. `xlsx` вне объёма MVP (ПЗ §4 — только HTML и PDF), но это фильтр загрузчика и обработка `unsupported content type` (ПЗ §6), а не основание назвать ссылку `IRRELEVANT`. Смешивать «нерелевантно» и «не поддерживается» запрещено: первое — свойство темы, второе — свойство MVP.

### 6.2. Влияние окружающего текста и DOM (п. 2 ответа БА)

| Контекст | Действие |
|---|---|
| `dom_container` ∈ {`nav`, `header`, `footer`} | Предусловие P-3 |
| `dom_container` = `main`/`article` | P-3 не применяется; `section_heading` получает вес сильного признака |
| `dom_container` = `aside` | `section_heading` даёт слабый признак |
| Список или таблица под заголовком с термином из `Q` | Все ссылки блока получают `topic_match` заголовка, если собственного термина у них нет |
| `surrounding_text` содержит термин из `Q` | Повышает `topic_match` с `none` до `partial`, но **не** до `direct` |

`section_heading` сильнее `surrounding_text`: заголовок относится к блоку намеренно, окружающий текст может быть случайным соседством.

### 6.3. Влияние `same_domain` и авторитетности источника (п. 6 ответа БА)

Три корзины в `domain_authority`:

| Корзина | Состав | Действие |
|---|---|---|
| `authoritative` | Домены регуляторов и наднациональных органов (`cnb.cz`, `bde.es`, `mnb.hu`, `esrb.europa.eu`, `eba.europa.eu`, `eur-lex.europa.eu`, `bis.org`, …) | Внешняя ссылка обрабатывается как внутренняя, без понижения |
| `neutral` | Всё, что не попало в две другие корзины | Класс понижается на одну ступень: `HIGH_VALUE` → `POTENTIALLY_RELEVANT`; `POTENTIALLY_RELEVANT` сохраняется |
| `excluded` | Соцсети, видеохостинги, CDN, счётчики, магазины | P-1 → `IRRELEVANT` |

`same_domain` вычисляется в T-008 по правилу из [OQ-013](open-questions.md#oq-013); таксономия его потребляет и не переопределяет. До закрытия OQ-013 корзины применяются к хосту из `target_url`.

## 7. Структура классификатора v1

```
classify(link, research_question, page) -> ClassifiedLink

1. prefilter(link)                  # P-0, может вернуть «не классифицируется»
2. features = extract(link, page)   # F-01…F-11
3. Q, V     = normalize_question(research_question)   # §3
4. if rule P-1 … P-5 matches: return its class        # §5, по порядку
5. group      = match_group(features)                 # §4 + tie-break
6. topic      = topic_match(features, Q, V)           # §3
7. cls        = MATRIX[group.rank][topic]             # §6
8. cls        = apply_authority(cls, features)        # §6.3
9. log(link, cls, matched_rule_ids)                   # BR-015, вход процесса §10
   return cls
```

Свойства, обязательные к соблюдению:

- **Детерминированность.** Один и тот же вход даёт один и тот же выход. LLM в v1 не вызывается — этим соблюдается принцип ПЗ §18 «детерминированные задачи не отдавать LLM».
- **Трассируемость.** Возвращается идентификатор сработавшего правила; без него процесс §10 неисполним.
- **Отсутствие правил в коде.** Все строки, шаблоны и списки — из `config/link_taxonomy.yaml`. Добавление правила не требует изменения Python-кода (п. 9 ответа БА).
- **Ровно один класс на ссылку.** BR-005 сохраняется.

## 8. Владелец таксономии (п. 8 ответа БА)

```
Owner: developer / project maintainer
```

Зафиксировано БА для MVP. Следствия, обязательные к соблюдению:

- Изменение справочника не требует нового `OQ` и согласования с БА, если оно проходит процесс §10.
- **LLM не изменяет production-правила** — ни автоматически, ни по предложению. LLM может использоваться как инструмент подготовки *предложения* правила, но запись в `config/link_taxonomy.yaml` делает человек (п. 8 ответа БА).
- Изменение самой **структуры** таксономии (перечень классов, перечень групп, матрица §6, порядок правил §5) владельцем справочника не покрывается: это возврат к БА через новый `OQ`.

## 9. Хранение справочника (п. 9 ответа БА)

Файл `config/link_taxonomy.yaml`, в Git, рядом с `config/settings.yaml`. Расширение структуры каталогов ПЗ §16 допустимо: §16 назван «Предлагаемая структура» ([D-009](decisions.md)).

Обязательные свойства: версия, синонимы, шаблоны, добавление правил без изменения crawler-кода.

```yaml
version: 1.0.0            # semver, обязателен, повышается процессом §10
updated: 2026-08-31
owner: project maintainer

stopwords: [the, a, of, in, for, and, or, what, is, are, how, which]

synonyms:                 # расширение терминов research_question
  ccyb:
    - countercyclical capital buffer
    - counter-cyclical capital buffer
    - CCyB
    - CCB
    - standard CCyB rate
    - positive neutral rate
    - neutral CCyB rate
  syrb: [systemic risk buffer, SyRB, systemic risk capital buffer]
  osii: [O-SII, other systemically important institution, D-SIB, domestic systemically important bank]

domain_vocabulary:        # общая предметная лексика -> topic_match = partial
  [macroprudential, capital buffer, systemic risk, financial stability,
   countercyclical, LTV, DSTI, DTI, LCR, NSFR, capital requirement]

generic_anchors: [download, read more, more, here, click here, link, pdf, open, view]

extensions:
  document: [pdf, doc, docx, pptx]
  data:     [xlsx, xls, csv, zip, 7z]
  ignore:   [jpg, jpeg, png, gif, svg, css, js, ico, woff, woff2, mp4]

groups:
  methodology:
    rank: primary
    anchor_strong: [methodology, methodological framework, technical note, annex]
    anchor_weak:   [approach, explanatory note]
    url_patterns:  ['/methodolog', '/framework']
  # … остальные группы §4 в том же формате

navigation_containers: [nav, header, footer, '[role=navigation]', .breadcrumb]

unrelated_topics:
  museum:  {anchor: [museum, exhibition, visitor centre, tours], url: ['/museum', '/visit']}
  numismatics: {anchor: [coins, banknote gallery, numismatics], url: ['/coins']}
  corporate:   {anchor: [procurement, tenders, sponsorship], url: ['/procurement']}

foreign_domains:          # чужие предметные области, правило P-5
  [monetary policy, payment systems, banknotes and coins,
   foreign exchange reserves, deposit insurance]

domain_authority:
  authoritative: [cnb.cz, bde.es, mnb.hu, esrb.europa.eu, eba.europa.eu,
                  eur-lex.europa.eu, bis.org, dnb.nl, nbs.rs, bankofengland.co.uk]
  excluded:      [facebook.com, x.com, twitter.com, linkedin.com, youtube.com,
                  instagram.com, google-analytics.com]
```

Список `authoritative` собран из хостов, уже перечисленных в [integrations.md, INT-01](../02_TECHNICAL/integrations.md#int-01-публичные-сайты-регуляторов). Он не является утверждённым тестовым датасетом — тот остаётся за [OQ-010](open-questions.md#oq-010).

## 10. Процесс обновления справочника (п. 10 ответа БА)

```
новая неизвестная ссылка
  → классификация (UNKNOWN или ошибочный класс)
  → логирование (BR-015: ссылка, класс, id сработавшего правила)
  → обнаружение ошибки на evaluation dataset (§12)
  → предложение нового правила
  → ручная проверка владельцем (§8)
  → добавление regression-теста в evaluation dataset
  → обновление config/link_taxonomy.yaml
  → повышение version (semver)
```

Правила процесса:

1. Изменение справочника без нового или изменённого теста в evaluation dataset не принимается.
2. `version` повышается при каждом изменении: patch — новые синонимы и строки; minor — новые группы или шаблоны; major — изменение матрицы §6 или порядка правил §5 (а это требует возврата к БА, см. §8).
3. Регрессия на существующих примерах — блокирующая: правило, ломающее ранее зелёный пример, не добавляется.
4. Рост доли `UNKNOWN` выше порога, зафиксированного в §12, — сигнал к пополнению справочника, а не к смене матрицы.

## 11. Примеры по категориям — набор правил, а не exhaustive dictionary

Прямое требование п. 11 ответа БА: перечни в §4 и в `config/link_taxonomy.yaml` — **типичные примеры и семантические признаки, а не закрытый словарь строк**. Классификатор обязан работать по нормализованным подстрокам и регулярным выражениям; совпадение по точному равенству строки запрещено как единственный механизм (п. 6 ответа БА).

Практическое следствие для реализации: тест «anchor `Methodology` → `HIGH_VALUE`» обязан проходить и для `Methodology of the countercyclical capital buffer`, и для `CCyB — methodological framework`, и для `Methodological note (PDF)`.

## 12. Evaluation dataset (п. 12 ответа БА)

Минимальный набор для проверки классификатора. Формат — из ответа БА. Хранение: `tests/fixtures/link_classification_cases.json`. Это **unit-фикстуры классификатора**, они не зависят от утверждения seed-датасета ([OQ-010](open-questions.md#oq-010)) и не заменяют его.

> **Честность данных.** Примеры синтетические: URL построены по шаблонам реально документированных хостов (см. §9), но их доступность не проверялась — сетевые запросы при подготовке спецификации не выполнялись.

```json
[
  {"id": "LC-01", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "Methodology",
   "target_url": "https://www.cnb.cz/en/financial-stability/macroprudential-policy/ccyb/methodology.pdf",
   "surrounding_context": "main / section: How the rate is determined", "expected_class": "HIGH_VALUE"},

  {"id": "LC-02", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "About the bank", "anchor_text": "Methodology",
   "target_url": "https://www.cnb.cz/en/about_cnb/museum/methodology-of-exhibitions/",
   "surrounding_context": "main / section: Museum and visitor centre", "expected_class": "IRRELEVANT",
   "rule": "P-2 — признак чужой темы в URL побеждает anchor text"},

  {"id": "LC-03", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "Download",
   "target_url": "https://www.cnb.cz/export/sites/cnb/en/files/ccyb-2026-q1.pdf",
   "surrounding_context": "main / heading: Countercyclical capital buffer methodology",
   "expected_class": "HIGH_VALUE", "rule": "P-4 — обобщённый anchor разрешается по заголовку"},

  {"id": "LC-04", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Home", "anchor_text": "Publications",
   "target_url": "https://www.cnb.cz/en/publications/", "surrounding_context": "nav / main menu",
   "expected_class": "NAVIGATION", "rule": "P-3 — related_material в навигационном контейнере"},

  {"id": "LC-05", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "Related publications",
   "target_url": "https://www.cnb.cz/en/financial-stability/publications/",
   "surrounding_context": "main / end of article", "expected_class": "POTENTIALLY_RELEVANT",
   "rule": "P-3 не применяется — dom_container = main"},

  {"id": "LC-06", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Press releases", "anchor_text": "Press release",
   "target_url": "https://www.cnb.cz/en/cnb-news/press-releases/CNB-raises-the-countercyclical-buffer-rate/",
   "surrounding_context": "main / list of releases", "expected_class": "HIGH_VALUE",
   "rule": "official_information + topic_match = direct по URL"},

  {"id": "LC-07", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Press releases", "anchor_text": "Press release",
   "target_url": "https://www.cnb.cz/en/cnb-news/press-releases/New-director-of-the-museum/",
   "surrounding_context": "main / list of releases", "expected_class": "IRRELEVANT", "rule": "P-2"},

  {"id": "LC-08", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Financial stability", "anchor_text": "Financial Stability Report 2026",
   "target_url": "https://www.bde.es/f/webbe/INF/MenuHorizontal/fsr-2026.pdf",
   "surrounding_context": "main / list of reports", "expected_class": "HIGH_VALUE"},

  {"id": "LC-09", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Financial stability", "anchor_text": "Capital buffers",
   "target_url": "https://www.bde.es/wbe/en/areas-actuacion/estabilidad-financiera/capital-buffers/",
   "surrounding_context": "main / section list", "expected_class": "POTENTIALLY_RELEVANT",
   "rule": "topic_landing (secondary) + partial"},

  {"id": "LC-10", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "Previous decisions",
   "target_url": "https://www.mnb.hu/en/financial-stability/ccyb/archive",
   "surrounding_context": "main / section: Decisions", "expected_class": "HIGH_VALUE",
   "rule": "archive (secondary) + direct по URL"},

  {"id": "LC-11", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Statistics", "anchor_text": "Data",
   "target_url": "https://www.mnb.hu/en/statistics/ccyb-rates.xlsx",
   "surrounding_context": "main / table of indicators", "expected_class": "HIGH_VALUE",
   "rule": "data (secondary) + direct; загрузка XLSX вне MVP — фильтр загрузчика, не класса"},

  {"id": "LC-12", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Home", "anchor_text": "Careers",
   "target_url": "https://www.mnb.hu/en/careers", "surrounding_context": "footer",
   "expected_class": "NAVIGATION", "rule": "ПЗ §9 относит careers к NAVIGATION"},

  {"id": "LC-13", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Home", "anchor_text": "Museum",
   "target_url": "https://www.mnb.hu/en/the-central-bank/visitor-centre",
   "surrounding_context": "main / promo block", "expected_class": "IRRELEVANT",
   "rule": "unrelated_topic, положительный признак"},

  {"id": "LC-14", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Home", "anchor_text": "Monetary policy",
   "target_url": "https://www.cnb.cz/en/monetary-policy/", "surrounding_context": "main / section list",
   "expected_class": "IRRELEVANT", "rule": "P-5 — чужая предметная область при topic_match ≠ direct"},

  {"id": "LC-15", "research_question": "How does monetary policy interact with the CCyB?",
   "source_page_topic": "Home", "anchor_text": "Monetary policy",
   "target_url": "https://www.cnb.cz/en/monetary-policy/", "surrounding_context": "main / section list",
   "expected_class": "POTENTIALLY_RELEVANT",
   "rule": "тот же вход, другой research_question — P-5 не срабатывает. Обязательный парный тест к LC-14"},

  {"id": "LC-16", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "See also",
   "target_url": "https://www.cnb.cz/en/financial-stability/", "surrounding_context": "aside / sidebar",
   "expected_class": "POTENTIALLY_RELEVANT"},

  {"id": "LC-17", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "More information",
   "target_url": "https://www.example-vendor.com/tools/", "surrounding_context": "footer / partner block",
   "expected_class": "UNKNOWN",
   "rule": "обобщённый anchor + контекст без группы + неавторитетный внешний домен"},

  {"id": "LC-18", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "Share on LinkedIn",
   "target_url": "https://www.linkedin.com/shareArticle?url=...", "surrounding_context": "main / share block",
   "expected_class": "IRRELEVANT", "rule": "P-1 — исключённый внешний домен"},

  {"id": "LC-19", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Countercyclical capital buffer", "anchor_text": "",
   "target_url": "https://www.esrb.europa.eu/pub/pdf/recommendations/ccyb-recommendation.pdf",
   "surrounding_context": "main / heading: ESRB recommendation on the countercyclical buffer",
   "expected_class": "HIGH_VALUE",
   "rule": "пустой anchor разрешается по заголовку (P-4); внешний авторитетный домен не понижает класс"},

  {"id": "LC-20", "research_question": "What is the current CCyB rate and how is it set?",
   "source_page_topic": "Financial stability", "anchor_text": "Consultation paper",
   "target_url": "https://www.eba.europa.eu/consultation/cp-2026-03",
   "surrounding_context": "main / list", "expected_class": "HIGH_VALUE"}
]
```

**Критерии приёмки классификатора на этом наборе (входят в T-009):**

1. 20 из 20 примеров дают ожидаемый класс.
2. Парные примеры LC-14 / LC-15 доказывают зависимость от `research_question` — без неё оба дадут одинаковый результат и один из них упадёт.
3. Ни один пример не получает `IRRELEVANT` по остаточному принципу: для каждого `IRRELEVANT` в наборе указан сработавший идентификатор правила.
4. Доля `UNKNOWN` на наборе ≤ 10 % (в наборе 1 из 20). Порог — стартовый ориентир владельца справочника, а не требование БА; повышается или снижается процессом §10.

## 13. Ожидаемое поведение для перечня anchor text из ответа БА (п. 13)

Базовое допущение таблицы: `research_question` — макропруденциальный (например, про CCyB), ссылка находится в контенте страницы регулятора соответствующей тематики. Столбец «Условия изменения» показывает, что класс не является свойством строки.

| Anchor text | Группа | Класс по умолчанию | Условия изменения |
|---|---|---|---|
| `Methodology` | methodology | `HIGH_VALUE` | `IRRELEVANT`, если URL ведёт в раздел чужой темы (P-2, LC-02) |
| `Methodological framework` | methodology | `HIGH_VALUE` | то же |
| `Official information` | official_information | `HIGH_VALUE` | `POTENTIALLY_RELEVANT` при `topic_match = none` |
| `Decision` | regulatory_decision | `HIGH_VALUE` | `POTENTIALLY_RELEVANT`, если решение не по теме вопроса |
| `Provision` | regulatory_decision | `HIGH_VALUE` | то же |
| `Financial Stability Report` | financial_report | `HIGH_VALUE` | остаётся `HIGH_VALUE` и в меню — P-3 не применяется к primary |
| `Macroprudential Report` | financial_report | `HIGH_VALUE` | то же |
| `Press release` | official_information | `HIGH_VALUE` при `direct`/`partial` | `POTENTIALLY_RELEVANT` для страницы-индекса релизов; `IRRELEVANT` при чужой теме в URL (LC-07) |
| `Consultation` | consultation | `HIGH_VALUE` | `POTENTIALLY_RELEVANT` при `topic_match = none` |
| `Opinion` | official_information | `HIGH_VALUE` | то же |
| `Research paper` | research | `HIGH_VALUE` | то же |
| `Data` | data | `POTENTIALLY_RELEVANT` | `HIGH_VALUE` при `direct` (LC-11) |
| `Download` | по контексту (P-4) | зависит от заголовка | `UNKNOWN`, если контекст не даёт группы |
| `Archive` | archive | `POTENTIALLY_RELEVANT` | `HIGH_VALUE` при `direct` |
| `Previous decisions` | archive + regulatory_decision | `HIGH_VALUE` при `direct`/`partial` | `POTENTIALLY_RELEVANT` при `none` |
| `Related documents` | related_material | `POTENTIALLY_RELEVANT` | `NAVIGATION` в навигационном контейнере (P-3) |
| `Related publications` | related_material | `POTENTIALLY_RELEVANT` | то же (LC-05) |
| `See also` | related_material | `POTENTIALLY_RELEVANT` | `UNKNOWN` вне контента и без темы страницы |
| `More information` | related_material (слабо) | `POTENTIALLY_RELEVANT` | `UNKNOWN` при отсутствии группы и темы (LC-17) |
| `Publications` | related_material | `POTENTIALLY_RELEVANT` в контенте | `NAVIGATION` в основном меню (P-3, LC-04) |
| `Home` | navigation | `NAVIGATION` | — |
| `Contact` | navigation | `NAVIGATION` | — |
| `Privacy` | navigation | `NAVIGATION` | — |
| `Careers` | navigation | `NAVIGATION` | по прямому указанию ПЗ §9, хотя тема служебная |
| `Museum` | unrelated_topic | `IRRELEVANT` | `UNKNOWN`, если в URL присутствует термин вопроса (P-2, исключение) |
| `Monetary policy` | unrelated (P-5) | `IRRELEVANT` | `POTENTIALLY_RELEVANT`/`HIGH_VALUE`, если вопрос касается ДКП (LC-15) |

## 14. Что осталось нерешённым

| Вопрос | Почему не решён здесь | Куда вынесен |
|---|---|---|
| По каким классам crawler переходит на depth 2 | Политика обхода, не таксономия. Влияет на бюджет 50 документов и на AC-09 | [OQ-029](open-questions.md#oq-029), БА |
| Что делать с `UNKNOWN` в MVP: игнорировать, обходить в последнюю очередь или отдавать LLM (ПЗ §18) | Затрагивает объём MVP и стоимость запуска | [OQ-029](open-questions.md#oq-029) |
| Правило вычисления `same_domain` | Свойство извлечения ссылок, не классификации | [OQ-013](open-questions.md#oq-013), техлид |
| Регистр значений enum (`HIGH_VALUE` против `high_value`) | Общее решение по схемам | [OQ-027](open-questions.md#oq-027) |

Ни один из них не блокирует реализацию классификатора: все четыре лежат вне его границ, зафиксированных в карточке [T-009](../03_IMPLEMENTATION/tasks.md#t-009).
