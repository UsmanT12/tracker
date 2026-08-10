"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { getPerformance } from "@/lib/api";
import type { PerformanceResponse } from "@/lib/types";
import { PerformanceChart } from "./performance-chart";
import { SeasonCalendar } from "./season-calendar";
import { SeasonSelect } from "./season-select";
import { StatSelector } from "./stat-selector";
import { StatSummary } from "./stat-summary";

export function PlayerPerformanceExplorer({
  initialPerformance,
  seasons,
}: {
  initialPerformance: PerformanceResponse;
  seasons: number[];
}) {
  const router = useRouter();
  const [performance, setPerformance] = useState(initialPerformance);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function update(season: number, stat: string) {
    setLoading(true);
    setError(null);
    try {
      const next = await getPerformance(performance.player.id, season, stat);
      setPerformance(next);
      router.replace(`?season=${season}&stat=${stat}`, { scroll: false });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load performance");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="player-header">
        <div>
          <p className="eyebrow">{performance.player.team.abbreviation ?? "WNBA"} · {performance.season}</p>
          <h1>{performance.player.display_name}</h1>
          <p className="player-meta">
            {performance.player.team.name} · {performance.summary.games_played} games played
          </p>
        </div>
        <div className="season-control">
          <SeasonSelect
            onChange={(season) => update(season, performance.stat.key)}
            seasons={seasons}
            value={performance.season}
          />
        </div>
      </header>

      <StatSelector
        disabled={loading}
        onChange={(stat) => update(performance.season, stat)}
        value={performance.stat.key}
      />
      {error ? <div className="error-state">{error}</div> : null}
      {loading ? <div className="loading">Recalculating the baseline…</div> : (
        <>
          <StatSummary performance={performance} />
          <section className="panel">
            <div className="panel-title">
              <h2>{performance.stat.label} by game</h2>
              <span>Dashed line = season average</span>
            </div>
            <PerformanceChart
              average={performance.summary.average}
              games={performance.games}
              stat={performance.stat}
            />
          </section>
          <SeasonCalendar
            key={`${performance.season}-${performance.stat.key}`}
            performance={performance}
          />
        </>
      )}
    </>
  );
}
