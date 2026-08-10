import { formatDate, formatDelta, formatStatValue } from "@/lib/formatting";
import type { PerformanceGame, StatMetadata } from "@/lib/types";

export function PerformanceGrid({
  games,
  stat,
}: {
  games: PerformanceGame[];
  stat: StatMetadata;
}) {
  return (
    <div className="performance-grid">
      {games.map((game) => (
        <article
          className={`performance-card ${game.comparison_bucket}`}
          key={game.game_id}
        >
          <div className="game-opponent">{game.is_home ? "vs" : "@"} {game.opponent}</div>
          <div className="game-date">{formatDate(game.date)}</div>
          <div className="game-value">
            {game.played ? formatStatValue(game.value, stat) : "DNP"}
          </div>
          <div className="game-delta">{formatDelta(game.delta, stat)}</div>
          <div className="comparison-label">{game.comparison_label}</div>
        </article>
      ))}
    </div>
  );
}

