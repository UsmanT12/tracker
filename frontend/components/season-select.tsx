"use client";

interface SeasonSelectProps {
  seasons: number[];
  value: number;
  onChange: (season: number) => void;
}

export function SeasonSelect({ seasons, value, onChange }: SeasonSelectProps) {
  return (
    <label>
      <span className="field-label">Season</span>
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

