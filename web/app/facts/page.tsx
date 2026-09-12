import type { Metadata } from "next";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { country } from "@/lib/countries";
import { BLOCK_LABELS, listFactsFiles } from "@/lib/facts";

export const metadata: Metadata = { title: "Извлечённые факты" };
// Static export: data/facts is read at build time; the daily Pages workflow rebuilds after each source check.

function ruDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
}

/** Transparent view of everything the pipeline has extracted so far: statement, verbatim quote, source, date. */
export default async function FactsPage() {
  const files = await listFactsFiles();
  const total = files.reduce((n, f) => n + f.facts.length, 0);
  const dropped = files.reduce((n, f) => n + f.dropped, 0);

  return (
    <>
      <SiteHeader languages={["ru"]} current="ru" linkHome />
      <div className="band status">
        <div className="in">
          {files.length === 0
            ? "Конвейер ещё не извлекал факты: папка data/facts пуста. Первый запуск ежедневной проверки с ключом API заполнит её."
            : `Источников прочитано: ${files.length}. Фактов с дословной цитатой: ${total}. Предложено моделью, но отброшено без подтверждённой цитаты: ${dropped}. Это сырьё для страниц коридоров, не консультация.`}
        </div>
      </div>
      <section className="section">
        <h2>Извлечённые факты</h2>
        <p className="lead">
          Каждая строка ниже прошла механическую проверку: цитата найдена дословно в тексте официальной страницы на
          момент снимка. Ежедневная проверка перечитывает источник и снимает статус, если цитата исчезла.
        </p>
        {files.map((file) => (
          <article key={file.url} style={{ marginTop: 28 }}>
            <h3 style={{ fontStyle: "normal", color: "var(--ink)" }}>
              <a href={file.url} target="_blank" rel="noopener noreferrer">
                {file.url}
              </a>
            </h3>
            <p className="hint">
              источник {file.source_id}
              {file.topic ? `, тема: ${file.topic}` : ""}; снимок {ruDate(file.fetched_at)}; фактов {file.facts.length}
              {file.dropped ? `, отброшено ${file.dropped}` : ""}
            </p>
            {file.facts.length === 0 && <p className="hint">На странице не найдено правил, ставок или программ с цитатой.</p>}
            <div className="facts">
              {file.facts.map((fact, i) => (
                <div className="fact" key={i}>
                  <div>
                    <p>{fact.statement.ru || fact.statement.en}</p>
                    <p className="hint" style={{ fontStyle: "italic" }}>
                      «{fact.quote}»
                    </p>
                  </div>
                  <span className="stamp ok">
                    <b>
                      {BLOCK_LABELS[fact.block] ?? fact.block}
                      {fact.country ? `, ${country(fact.country).name}` : ""}
                    </b>
                    цитата подтверждена {ruDate(file.fetched_at)}
                    {fact.hs_scope.length ? `; HS ${fact.hs_scope.join(", ")}` : ""}
                  </span>
                </div>
              ))}
            </div>
          </article>
        ))}
      </section>
      <SiteFooter />
    </>
  );
}
