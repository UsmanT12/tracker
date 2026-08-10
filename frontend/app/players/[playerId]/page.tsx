import Link from "next/link";

import { PlayerPerformanceExplorer } from "@/components/player-performance-explorer";
import { getPerformance, getSeasons } from "@/lib/api";

export default async function PlayerPage({
  params,
  searchParams,
}: {
  params: Promise<{ playerId: string }>;
  searchParams: Promise<{ season?: string; stat?: string }>;
}) {
  const [{ playerId }, query] = await Promise.all([params, searchParams]);
  try {
    const seasons = await getSeasons();
    const season = Number(query.season) || seasons.default_season;
    if (!season) {
      throw new Error("No season data is available");
    }
    const performance = await getPerformance(playerId, season, query.stat ?? "pts");
    return (
      <div className="container">
        <Link className="back-link" href="/">← Player index</Link>
        <PlayerPerformanceExplorer
          initialPerformance={performance}
          seasons={seasons.seasons}
        />
      </div>
    );
  } catch (error) {
    return (
      <div className="container">
        <Link className="back-link" href="/">← Player index</Link>
        <div className="error-state">
          {error instanceof Error ? error.message : "Unable to load this player"}
        </div>
      </div>
    );
  }
}

