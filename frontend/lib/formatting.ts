import type { StatMetadata } from "./types";

export function formatStatValue(value: number | null, stat: StatMetadata): string {
  if (value === null) return "—";
  const formatted = value.toFixed(stat.precision);
  return stat.unit === "percentage" ? `${formatted}%` : formatted;
}

export function formatDelta(delta: number | null, stat: StatMetadata): string {
  if (delta === null) return "—";
  const suffix = stat.unit === "percentage" ? " pp" : "";
  const rounded = Number(delta.toFixed(stat.precision));
  return `${rounded >= 0 ? "+" : ""}${rounded.toFixed(stat.precision)}${suffix}`;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}
