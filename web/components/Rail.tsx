"use client";

import Link from "next/link";
import { useState } from "react";
import type { PageContent } from "@/lib/page-content";

export interface TocItem {
  id: string;
  number?: number;
  title: string;
}

function Toc({ items }: { items: TocItem[] }) {
  return (
    <div className="rail-block toc-block">
      <h4>На этой странице</h4>
      <ul className="toc">
        {items.map((item) => (
          <li key={item.id}>
            <a href={`#${item.id}`}>
              <span className="n">{item.number ?? ""}</span>
              {item.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Legend() {
  return (
    <div className="rail-block">
      <h4>Цвета на странице</h4>
      <p className="legend">
        <span className="sw ban" />
        запрет или санкции
      </p>
      <p className="legend">
        <span className="sw warn" />
        препятствие или требует проверки
      </p>
      <p className="legend">
        <span className="sw ok" />
        выгода
      </p>
    </div>
  );
}

/**
 * "Следить за коридором". Stage 0: the form works, the subscription is not stored yet (stage 3 wires it to
 * the `subscriptions` table and the monitor). The demo state says so explicitly.
 */
export function FollowPanel({ sample }: { sample?: string }) {
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState(false);
  const [email, setEmail] = useState("");

  return (
    <div className="rail-block">
      {done ? (
        <div className="notice">
          <p>
            <b>Подписка оформлена</b> — уведомления по этому коридору будут приходить на указанный адрес (демо:
            подписки пока не сохраняются).
          </p>
          {sample && <p className="sample">Пример письма: {sample}</p>}
        </div>
      ) : (
        <>
          <button type="button" className="follow" onClick={() => setOpen((v) => !v)}>
            {open ? "Свернуть" : "Следить за коридором"}
          </button>
          <div className="fp" hidden={!open}>
            <p className="fp-title">О чём сообщать</p>
            <label>
              <input type="checkbox" defaultChecked /> пошлины, налоги и квоты
            </label>
            <label>
              <input type="checkbox" defaultChecked /> санкции и запреты
            </label>
            <label>
              <input type="checkbox" defaultChecked /> новые программы и субсидии
            </label>
            <label>
              <input type="checkbox" /> дедлайны отборов и заявок
            </label>
            <label>
              <input type="checkbox" /> изменение оценки коридора
            </label>
            <p className="fp-title" style={{ marginTop: 10 }}>
              Как часто
            </p>
            <label>
              <input type="radio" name="freq" defaultChecked /> сразу, как обнаружено
            </label>
            <label>
              <input type="radio" name="freq" /> раз в неделю, сводкой
            </label>
            <input
              type="email"
              placeholder="ваш email"
              aria-label="Email для уведомлений"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <button type="button" className="report" onClick={() => setDone(true)}>
              Подписаться
            </button>
            <p className="sub">
              Уведомление приходит, когда конвейер перечитал официальный источник и нашёл изменение — со ссылкой на
              источник и датой. Без изменений писем нет.
            </p>
          </div>
        </>
      )}
      <p>Подписка — на этот коридор и товар. Другие коридоры добавляются отдельно.</p>
    </div>
  );
}

/** "Сообщить об ошибке" triggers an automatic re-check of the page's sources (stage 3: `error_reports`). */
export function ReportError() {
  const [done, setDone] = useState(false);
  return (
    <div className="rail-block">
      {done ? (
        <div className="report-done">
          Принято. Источники по странице будут перечитаны, изменения появятся здесь (демо: перепроверка пока не
          запускается).
        </div>
      ) : (
        <button type="button" className="report" onClick={() => setDone(true)}>
          Сообщить об ошибке
        </button>
      )}
      <p>Запускает автоматическую перепроверку источников по этой странице. Ответ вернётся сюда же.</p>
    </div>
  );
}

export interface SupplyLink {
  href: string;
  label: string;
  note: string;
}

export function Rail({
  toc,
  rail,
  hideFollow,
  supplyLink,
}: {
  toc: TocItem[];
  rail: PageContent["rail"];
  /** The "where to buy" page has no per-corridor subscription yet. */
  hideFollow?: boolean;
  /** Link to the "where to buy" page for the export country and product group, when one exists. */
  supplyLink?: SupplyLink;
}) {
  return (
    <aside className="rail">
      <Toc items={toc} />
      <Legend />
      {supplyLink && (
        <div className="rail-block">
          <h4>Где производят</h4>
          <p style={{ marginTop: 0 }}>
            <Link href={supplyLink.href}>{supplyLink.label}</Link>
          </p>
          <p>{supplyLink.note}</p>
        </div>
      )}
      {!hideFollow && <FollowPanel sample={rail.followSample ?? undefined} />}
      <ReportError />
      <div className="rail-block">
        <p style={{ marginTop: 0 }}>{rail.disclaimer}</p>
        {rail.reverseLabel && (
          <p>
            <a className="dim" href="#" title="Обратные направления — после MVP" onClick={(e) => e.preventDefault()}>
              {rail.reverseLabel}
            </a>
          </p>
        )}
      </div>
    </aside>
  );
}
