"use client";

interface SeasonSelectProps {
  seasons: number[];
  value: number;
  onChange: (season: number) => void;
  hideLabel?: boolean;
}

export function SeasonSelect({ seasons, value, onChange, hideLabel = false }: SeasonSelectProps) {
  return (
    <label>
      <span className={hideLabel ? "sr-only" : "field-label"}>Season</span>
      <select
        aria-label="Season"
        className="select"
        onChange={(event) => onChange(Number(event.target.value))}
        value={value}
      >
        {seasons.map((season) => (
          <option key={season} value={season}>{season}</option>
        ))}
      </select>
    </label>
  );
}

