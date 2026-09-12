"use client";

import { useState } from "react";
import type { Calculator, Mode } from "@/lib/page-content";
import { evaluateLines, formatAmount, initialValues, resolveLabel, type CalcValues } from "@/lib/calc";
import { visibleInMode } from "@/lib/text";
import { SectionHeading } from "./Section";

/** "Сколько платить государствам": lines and rates come from page content; this component only does arithmetic. */
export function CostCalculator({ calc, mode }: { calc: Calculator; mode: Mode }) {
  const [values, setValues] = useState<CalcValues>(() => initialValues(calc.inputs));
  const lines = evaluateLines(calc.lines, values, mode);
  const total = calc.lines.reduce((sum, line) => sum + (lines[line.id] ?? 0), 0);

  function set(id: string, value: number | boolean) {
    setValues((prev) => ({ ...prev, [id]: value }));
  }

  return (
    <>
      <SectionHeading id={calc.id} number={calc.number} title={calc.title} />
      <p className="lead">{calc.lead}</p>
      {calc.lines.length === 0 ? (
        <p className="hint">{calc.note}</p>
      ) : (
      <div className="calc">
        {calc.inputs
          .filter((input) => visibleInMode(input.modes, mode))
          .map((input, i) => {
            const inputId = `calc-${calc.id}-${input.id}`;
            const style = i > 0 ? { marginTop: 10 } : undefined;
            if (input.kind === "checkbox") {
              return (
                <label key={input.id} style={style}>
                  <input
                    id={inputId}
                    type="checkbox"
                    checked={Boolean(values[input.id])}
                    onChange={(e) => set(input.id, e.target.checked)}
                    style={{ width: 18, height: 18, accentColor: "var(--ink)" }}
                  />
                  {input.label}
                </label>
              );
            }
            if (input.kind === "select") {
              return (
                <label key={input.id} style={style}>
                  {input.label}
                  <select
                    id={inputId}
                    className="inline-select"
                    value={String(values[input.id])}
                    onChange={(e) => set(input.id, Number(e.target.value))}
                  >
                    {input.options?.map((o) => (
                      <option key={o.label} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </label>
              );
            }
            return (
              <label key={input.id} style={style}>
                {input.label}
                <input
                  id={inputId}
                  type="number"
                  min={input.min ?? 0}
                  step={input.step}
                  value={Number(values[input.id])}
                  onChange={(e) => set(input.id, parseFloat(e.target.value) || 0)}
                />
              </label>
            );
          })}
        <table>
          <tbody>
            {calc.lines.map((line) => (
              <tr key={line.id}>
                <td>{resolveLabel(line.label, values, mode, calc.inputs)}</td>
                <td>{formatAmount(lines[line.id] ?? 0)}</td>
              </tr>
            ))}
            <tr className="total">
              <td>{calc.totalLabel}</td>
              <td>
                {formatAmount(total)} {calc.currency}
              </td>
            </tr>
          </tbody>
        </table>
        <p className="sub" style={{ margin: "10px 0 0" }}>
          {calc.note}
        </p>
      </div>
      )}
    </>
  );
}
