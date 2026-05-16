import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { RiskLevel } from "@/types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

const RISK_COLOR: Record<string, string> = {
  low: "var(--color-green)",
  medium: "var(--color-amber)",
  high: "var(--color-red)",
};

const RISK_SOFT_COLOR: Record<string, string> = {
  low: "var(--color-green-soft)",
  medium: "var(--color-amber-soft)",
  high: "var(--color-red-soft)",
};

export function riskToColor(risk: string | RiskLevel | undefined): string {
  if (!risk) return "var(--color-warm-gray)";
  return RISK_COLOR[risk.toLowerCase()] ?? "var(--color-warm-gray)";
}

export function riskToSoftColor(risk: string | RiskLevel | undefined): string {
  if (!risk) return "var(--color-warm-gray-soft)";
  return RISK_SOFT_COLOR[risk.toLowerCase()] ?? "var(--color-warm-gray-soft)";
}

export function truncate(text: string, max = 140): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trimEnd()}…`;
}

export function formatDate(value: string | number | Date | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return String(value);
  }
}

export function formatRelative(value: string | number | Date | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  const delta = Math.round((Date.now() - date.getTime()) / 1000);
  const units: Array<[number, string]> = [
    [60, "sec"],
    [60, "min"],
    [24, "hr"],
    [7, "day"],
    [4.345, "wk"],
    [12, "mo"],
    [Infinity, "yr"],
  ];
  let value_ = delta;
  let unit = "sec";
  for (const [size, label] of units) {
    if (Math.abs(value_) < size) {
      unit = label;
      break;
    }
    value_ = value_ / size;
    unit = label;
  }
  const rounded = Math.round(value_);
  return rounded === 0 ? "just now" : `${rounded} ${unit} ago`;
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return "—";
  return `${Math.round(score * 100)}%`;
}

export function uid(prefix = "id"): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
