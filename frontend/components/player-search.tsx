"use client";

import Link from "next/link";
import { ArrowUpRight, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { getPlayers } from "@/lib/api";
import type { PlayerListItem } from "@/lib/types";
import { SeasonSelect } from "./season-select";

interface PlayerSearchProps {
  initialPlayers: PlayerListItem[];
  initialTotal: number;
  seasons: number[];
  initialSeason: number;
}

export function PlayerSearch({
  initialPlayers,
  initialTotal,
  seasons,
  initialSeason,
}: PlayerSearchProps) {
  const [players, setPlayers] = useState(initialPlayers);
  const [total, setTotal] = useState(initialTotal);
  const [season, setSeason] = useState(initialSeason);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (season === initialSeason && search === "") {
      setPlayers(initialPlayers);
      setTotal(initialTotal);
      return;
    }
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getPlayers({ season, search });
        setPlayers(response.items);
        setTotal(response.total);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Unable to load players");
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [initialPlayers, initialSeason, initialTotal, search, season]);

  return (
    <section aria-label="Players">
      <div className="toolbar">
        <label>
          <span className="sr-only">Find a player</span>
          <span className="search-wrap">
            <Search size={19} aria-hidden="true" />
            <input
              className="input"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by player name"
              type="search"
              value={search}
            />
          </span>
        </label>
        <SeasonSelect hideLabel seasons={seasons} value={season} onChange={setSeason} />
      </div>
      <div className="section-heading player-results" role="status">
        <span>{loading ? "Updating…" : `${total} players`}</span>
      </div>
      {error ? <div className="error-state">{error}</div> : null}
      {!error && players.length === 0 ? (
        <div className="empty-state">No players match this search for {season}.</div>
      ) : null}
      {!error && players.length > 0 ? (
        <div className="player-grid">
          {players.map((player) => (
            <Link
              className="player-card"
              href={`/players/${player.id}?season=${season}&stat=pts`}
              key={player.id}
            >
              <div className="player-card-heading">
                <span className="player-team">
                  {player.team_name ?? player.team_abbreviation ?? "WNBA"}
                </span>
                <ArrowUpRight size={17} aria-hidden="true" />
              </div>
              <div className="player-name">{player.display_name}</div>
              <div className="mini-stats">
                <span><strong>{player.ppg?.toFixed(1) ?? "—"}</strong><small>PPG</small></span>
                <span><strong>{player.rpg?.toFixed(1) ?? "—"}</strong><small>RPG</small></span>
                <span><strong>{player.apg?.toFixed(1) ?? "—"}</strong><small>APG</small></span>
              </div>
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  );
}

