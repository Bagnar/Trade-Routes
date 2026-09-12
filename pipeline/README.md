# Конвейер — каркас

Модули соответствуют компонентам из `docs/concept.md`, раздел 8. Каждый запускается отдельно на одном коридоре и одной товарной группе:

    python -m pipeline fetch    --corridor cn-ca --hs6 610910
    python -m pipeline extract  --corridor cn-ca --hs6 610910
    python -m pipeline rates    --country CA --hs6 610910
    python -m pipeline validate --corridor cn-ca --hs6 610910
    python -m pipeline assemble --corridor cn-ca --hs6 610910 --lang ru
    python -m pipeline index    --hs6 610910
    python -m pipeline monitor
    python -m pipeline supply   --country CN --hs6 843280

| Модуль | Отвечает за | Правило, которое нельзя нарушить |
|---|---|---|
| `registry.py` | чтение `data/sources.yaml`, синхронизация с таблицами `sources`, `source_urls` | только домены из реестра |
| `fetch.py` | загрузка страниц, снимки с хешем и датой, повторные попытки, лимиты вежливости | не ходить за пределы белого списка |
| `extract.py` | из снимка — факты по блокам с цитатой через LLM API | факт без цитаты отбрасывается |
| `rates.py` | импорт тарифных таблиц и приложений к соглашениям в `rates` | LLM не пишет числа |
| `validate.py` | сверка чисел со ставками, санкционная проверка, свежесть, полнота блоков, фильтр формулировок «как обойти» | тесты обязательны |
| `assemble.py` | сборка страницы из фактов по шаблону; текст на каждом языке из одного набора фактов | печать источника у каждой строки |
| `index.py` | индексный слой и оценка из пяти частей | спрос и логистика — только «ориентир» |
| `monitor.py` | перечитывание источников, сравнение снимков, пересборка, уведомления | без изменений — без писем |
| `supply.py` | слой «Где купить»: регионы и кластеры, официальные реестры и выставки, показатели из статистики; страницы `supply_pages` | только регионы и официальные реестры, никаких компаний; числа только из статистических таблиц |

Реализовано (этап 1, первая часть): `registry.py`, `fetch.py`, `extract.py`, `validate.py` (с тестами в `tests/`), `monitor.py`.
Заглушки: `rates.py`, `assemble.py`, `index.py`, `supply.py`.

    python -m pipeline fetch    --url https://www.cbsa-asfc.gc.ca/publications/dm-md/d9/d9-1-6-eng.html
    python -m pipeline extract  --url <url из белого списка> --topic forced_labour   # нужен ANTHROPIC_API_KEY
    python -m pipeline extract  --registry [--country CA]                             # все urls из data/sources.yaml → data/facts
    python -m pipeline validate                                                        # белый список, цитаты, числа, формулировки
    python -m pipeline monitor                                                         # перечитать источники, проверить цитаты, data/monitor-report.md
    python -m pytest pipeline/tests

Ежедневный запуск — `.github/workflows/daily-check.yml` (monitor → extract при наличии ключа → validate → коммит).
Из-под GitHub Actions официальные сайты доступны; из облачной сессии Claude Code они закрыты сетевой политикой.
