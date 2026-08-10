"use client";

export const SELECTABLE_STATS = [
  ["pts", "PTS"],
  ["reb", "REB"],
  ["ast", "AST"],
  ["fg3m", "3PM"],
  ["stl", "STL"],
  ["blk", "BLK"],
  ["tov", "TOV"],
  ["minutes", "MIN"],
  ["fg_pct", "FG%"],
  ["fg3_pct", "3P%"],
  ["ft_pct", "FT%"],
  ["plus_minus", "+/-"],
] as const;

interface StatSelectorProps {
  value: string;
  onChange: (stat: string) => void;
  disabled?: boolean;
}

export function StatSelector({ value, onChange, disabled }: StatSelectorProps) {
  return (
    <div className="stat-tabs" aria-label="Statistic" role="tablist">
      {SELECTABLE_STATS.map(([key, label]) => (
        <button
          aria-selected={value === key}
          className={`stat-tab ${value === key ? "active" : ""}`}
          disabled={disabled}
          key={key}
          onClick={() => onChange(key)}
          role="tab"
          type="button"
        >
          {label}
        </button>
      ))}
    </div>
  );
}

