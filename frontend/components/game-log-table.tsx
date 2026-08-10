"use client";

import { useMemo, useState } from "react";

import { formatDate, formatDelta, formatStatValue } from "@/lib/formatting";
import type { PerformanceGame, StatMetadata } from "@/lib/types";

export function GameLogTable({
  games,
  stat,
}: {
  games: PerformanceGame[];
  stat: StatMetadata;
}) {
  const [sort, setSort] = useState<"date" | "value">("date");
  const sorted = useMemo(
    () =>
      [...games].sort((a, b) =>
        sort === "date"
          ? b.date.localeCompare(a.date)
          : (b.value ?? Number.NEGATIVE_INFINITY) - (a.value ?? Number.NEGATIVE_INFINITY),
      ),
    [games, sort],
  );

  return (
    <div className="table-wrap">
      <table className="game-table">
        <thead>
          <tr>
            <th onClick={() => setSort("date")}>Date</th>
            <th>Opponent</th>
            <th>H/A</th>
            <th>Minutes</th>
            <th className="selected-column" onClick={() => setSort("value")}>
              {stat.short_label}
            </th>
            <th>Average</th>
            <th>Delta</th>
            <th>Result</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((game) => (
            <tr key={game.game_id}>
              <td>{formatDate(game.date)}</td>
              <td>{game.opponent}</td>
              <td>{game.is_home === null ? "—" : game.is_home ? "Home" : "Away"}</td>
              <td>{game.played ? game.minutes.toFixed(1) : "DNP"}</td>
              <td className="selected-column">
                {game.played ? formatStatValue(game.value, stat) : "DNP"}
              </td>
              <td>{formatStatValue(game.average, stat)}</td>
              <td className={
                game.delta === null ? "" : game.delta >= 0 ? "delta-positive" : "delta-negative"
              }>
                {formatDelta(game.delta, stat)}
              </td>
              <td>{game.result ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

