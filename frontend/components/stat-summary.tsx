import { formatStatValue } from "@/lib/formatting";
import type { PerformanceResponse } from "@/lib/types";

export function StatSummary({ performance }: { performance: PerformanceResponse }) {
  const { stat, summary } = performance;
  const latest = [...performance.games].reverse().find((game) => game.value !== null);
  return (
    <section className="summary-grid" aria-label={`${stat.label} season summary`}>
      <div className="summary-card primary">
        <span>Season average</span>
        <strong>{formatStatValue(summary.average, stat)}</strong>
      </div>
      <div className="summary-card">
        <span>Season high</span>
        <strong>{formatStatValue(summary.high, stat)}</strong>
      </div>
      <div className="summary-card">
        <span>Season low</span>
        <strong>{formatStatValue(summary.low, stat)}</strong>
      </div>
      <div className="summary-card">
        <span>Latest game</span>
        <strong>{formatStatValue(latest?.value ?? null, stat)}</strong>
      </div>
    </section>
  );
}

