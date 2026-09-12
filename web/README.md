# web/ — фронтенд

Next.js 16 + TypeScript (App Router). Структура и стиль — из `../mockups/`: `app/globals.css` перенесён из макетов дословно, компоненты повторяют их разметку.

## Запуск

    npm install
    npm run dev          # http://localhost:3000
    npm run typecheck    # tsc --noEmit
    npm run lint         # eslint
    npm run build        # production build

## Как устроено

- `lib/page-content.ts` — **шаблон страницы коридора как структура данных**: тип `PageContent` описывает содержимое `pages.content` (JSONB). Конвейер (`assemble`) обязан выдавать ровно эту форму; фронтенд факты не собирает.
- `scripts/scaffold_demo_pages.py` (в корне репозитория) — генерирует заготовки для всех товарных групп из `data/corridors.yaml`: строки о паре стран берутся из рукописных демо-страниц, всё товарное помечено «не собрано» (`not_found`), калькулятор пуст до загрузки ставок. Рукописные страницы (`cn-ca-610910`, `ru-ir-100199`, `cn-6109`, `cn-8432`, `tr-6109`) генератор не трогает.
- `lib/pages.ts` — хранилище страниц. Этап 0: JSON-фикстуры в `data/pages/` (все `isDemo: true`, взяты из макетов, цифры иллюстративные). Этап 3: те же функции читают таблицу `pages`.
- `lib/corridors.ts` — читает `../data/corridors.yaml` (единственный источник списка коридоров).
- `lib/calc.ts` — калькулятор «сколько платить»: выражения из JSON (`mul`, `add`, `div`, `if`, `mode`), без `eval`; ставки приходят из содержимого страницы, не из кода.
- `app/page.tsx` — стартовая: фраза-запрос, маршрутизация в открытые коридоры, карточки, «как собираются страницы».
- `app/corridor/[corridor]/[hs6]/page.tsx` — страница коридора; `?mode=parcel` включает режим посылок.
- `app/where-to-buy/page.tsx` и `app/where-to-buy/[country]/[hs]/page.tsx` — слой «Где купить» (`docs/where-to-buy.md`): регионы и кластеры производства, официальные реестры и выставки, что проверить, ссылки на коридоры. Тип содержимого — `lib/supply-content.ts`, хранилище — `lib/supply.ts` (фикстуры в `data/supply/`, все `isDemo: true`). На странице коридора в боковой панели появляется ссылка «Где производят», если для страны вывоза и группы есть такая страница.

Компоненты (`components/`): `QuerySentence`, `Bands` (StatusBand, DemoBand, SanctionsBand), `SourceStamp`, `FactRow`, `Section`, `Summary`, `RatingCard` (+ `ProsCons`), `CompareTable`, `CostCalculator`, `DocumentChecklist`, `SourcesTable`, `Rail` (оглавление, легенда, `FollowPanel`, `ReportError`), `SiteHeader`/`SiteFooter`, `SearchForm`, `CorridorPage`, `SupplyPage`, `BuySearch`.

Подписка, «сообщить об ошибке» и запрос коридора пока ничего не сохраняют и говорят об этом на экране — API и таблицы подключаются на этапе 3.
