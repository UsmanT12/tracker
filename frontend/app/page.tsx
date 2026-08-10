import { Database, RefreshCw } from "lucide-react";

import { PlayerSearch } from "@/components/player-search";
import { getDataStatus, getPlayers, getSeasons } from "@/lib/api";
import { formatDate } from "@/lib/formatting";

export default async function HomePage() {
  try {
    const seasons = await getSeasons();
    const season = seasons.default_season;
    const [players, status] = await Promise.all([
      getPlayers({ season: season ?? undefined }),
      getDataStatus(),
    ]);

    return (
      <div className="container">
        <section className="hero">
          <div>
            <p className="eyebrow">Performance, put in context</p>
            <h1>Every game against the baseline.</h1>
            <p className="hero-copy">
              Explore how each WNBA performance rises above—or falls below—a
              player&apos;s season average. Switch the metric and the whole story updates.
            </p>
          </div>
          <aside className="status-card" aria-label="Data status">
            <div className="status-label"><span className="status-dot" />Data available through</div>
            <div className="status-date">
              {status.latest_game_date ? formatDate(status.latest_game_date) : "No games imported"}
            </div>
            <div className="status-counts">
              <div><strong>{status.players}</strong><span>Players</span></div>
              <div><strong>{status.games}</strong><span>Games</span></div>
              <div><strong>{status.player_stat_rows}</strong><span>Stat lines</span></div>
            </div>
          </aside>
        </section>
        {season ? (
          <PlayerSearch
            initialPlayers={players.items}
            initialSeason={season}
            initialTotal={players.total}
            seasons={seasons.seasons}
          />
        ) : (
          <div className="empty-state">
            <Database size={24} aria-hidden="true" />
            <p>No seasons are available yet. Run the scraper or legacy migration first.</p>
          </div>
        )}
      </div>
    );
  } catch {
    return (
      <div className="container">
        <section className="hero">
          <div>
            <p className="eyebrow">Performance, put in context</p>
            <h1>Every game against the baseline.</h1>
          </div>
        </section>
        <div className="error-state">
          <RefreshCw size={24} aria-hidden="true" />
          <p>The statistics API is unavailable. Start the backend and refresh this page.</p>
        </div>
      </div>
    );
  }
}

