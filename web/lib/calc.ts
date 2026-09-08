/**
 * Evaluator for the calculator's data-driven expressions (see Calculator in page-content.ts).
 * Pure functions, no eval: the only numbers that ever appear come from the page content (rates layer).
 */
import type { CalcExpr, CalcInput, CalcLabel, CalcLine, Mode } from "./page-content";

export type CalcValues = Record<string, number | boolean>;

export function initialValues(inputs: CalcInput[]): CalcValues {
  const values: CalcValues = {};
  for (const input of inputs) values[input.id] = input.value;
  return values;
}

export function evaluate(expr: CalcExpr, values: CalcValues, mode: Mode, lines: Record<string, number>): number {
  if (typeof expr === "number") return expr;
  if ("input" in expr) return Number(values[expr.input] ?? 0);
  if ("line" in expr) return lines[expr.line] ?? 0;
  if ("mul" in expr) return expr.mul.reduce<number>((acc, e) => acc * evaluate(e, values, mode, lines), 1);
  if ("add" in expr) return expr.add.reduce<number>((acc, e) => acc + evaluate(e, values, mode, lines), 0);
  if ("div" in expr) {
    const d = evaluate(expr.div[1], values, mode, lines);
    return d === 0 ? 0 : evaluate(expr.div[0], values, mode, lines) / d;
  }
  if ("if" in expr) return evaluate(values[expr.if] ? expr.then : expr.else, values, mode, lines);
  if ("mode" in expr) return evaluate(expr.mode[mode], values, mode, lines);
  return 0;
}

/** Evaluates all lines in order; a line may reference lines defined before it. */
export function evaluateLines(lines: CalcLine[], values: CalcValues, mode: Mode): Record<string, number> {
  const result: Record<string, number> = {};
  for (const line of lines) result[line.id] = evaluate(line.expr, values, mode, result);
  return result;
}

export function resolveLabel(label: CalcLabel, values: CalcValues, mode: Mode, inputs: CalcInput[]): string {
  if (typeof label === "string") return label;
  if ("if" in label) return resolveLabel(values[label.if] ? label.then : label.else, values, mode, inputs);
  if ("mode" in label) return resolveLabel(label.mode[mode], values, mode, inputs);
  const input = inputs.find((i) => i.id === label.select);
  const option = input?.options?.find((o) => o.value === Number(values[label.select]));
  return label.template
    .replace("{short}", option?.short ?? option?.label ?? "")
    .replace("{label}", option?.label ?? "");
}

export function formatAmount(n: number, locale = "ru-RU"): string {
  return Math.round(n).toLocaleString(locale);
}
