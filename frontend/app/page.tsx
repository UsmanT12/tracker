import { Database, RefreshCw } from "lucide-react";

import { PlayerSearch } from "@/components/player-search";
import { getPlayers, getSeasons } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  try {
    const seasons = await getSeasons();
    const season = seasons.default_season;
    const players = season ? await getPlayers({ season }) : null;

    return (
      <div className="container home-container">
        <header className="home-heading">
          <h1>Players</h1>
        </header>
        {season && players ? (
          <PlayerSearch
            initialPlayers={players.items}
            initialSeason={season}
            initialTotal={players.total}
            seasons={seasons.seasons}
          />
        ) : (
          <div className="empty-state">
            <Database size={24} aria-hidden="true" />
            <p>No player data is available yet.</p>
          </div>
        )}
      </div>
    );
  } catch {
    return (
      <div className="container home-container">
        <header className="home-heading">
          <h1>Players</h1>
        </header>
        <div className="error-state">
          <RefreshCw size={24} aria-hidden="true" />
          <p>The statistics service is temporarily unavailable. Please try again shortly.</p>
        </div>
      </div>
    );
  }
}

