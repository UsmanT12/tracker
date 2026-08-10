"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatDate, formatDelta, formatStatValue } from "@/lib/formatting";
import type { PerformanceGame, StatMetadata } from "@/lib/types";

const COLORS: Record<string, string> = {
  strong_above: "#55d49f",
  above: "#78bda0",
  near_average: "#d9b86c",
  below: "#d87986",
  strong_below: "#ff667b",
};

function ChartTooltip({
  active,
  payload,
  stat,
}: {
  active?: boolean;
  payload?: ReadonlyArray<{ payload: PerformanceGame }>;
  stat: StatMetadata;
}) {
  const game = payload?.[0]?.payload;
  if (!active || !game) return null;
  return (
    <div className="chart-tooltip">
      <strong>{game.is_home ? "vs" : "@"} {game.opponent} · {formatDate(game.date)}</strong>
      <span>{formatStatValue(game.value, stat)} · {formatDelta(game.delta, stat)}</span>
      <span>{game.comparison_label}</span>
    </div>
  );
}

export function PerformanceChart({
  games,
  stat,
  average,
}: {
  games: PerformanceGame[];
  stat: StatMetadata;
  average: number | null;
}) {
  const chartGames = games.filter((game) => game.value !== null);
  if (chartGames.length === 0) {
    return <div className="empty-state">No valid values are available for this metric.</div>;
  }
  return (
    <div className="chart-wrap" aria-label={`${stat.label} performance chart`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartGames} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid stroke="#302b3d" strokeDasharray="3 5" vertical={false} />
          <XAxis
            axisLine={false}
            dataKey="date"
            fontSize={10}
            stroke="#8e879c"
            tickFormatter={(value: string) => value.slice(5)}
            tickLine={false}
          />
          <YAxis axisLine={false} fontSize={10} stroke="#8e879c" tickLine={false} />
          <Tooltip
            content={<ChartTooltip stat={stat} />}
            cursor={{ fill: "rgba(255,255,255,.035)" }}
          />
          {average !== null ? (
            <ReferenceLine
              label={{ value: "AVG", fill: "#bba7f8", fontSize: 10, position: "insideTopRight" }}
              stroke="#9d7cff"
              strokeDasharray="5 5"
              y={average}
            />
          ) : null}
          <Bar dataKey="value" maxBarSize={26} radius={[5, 5, 0, 0]}>
            {chartGames.map((game) => (
              <Cell
                fill={COLORS[game.comparison_bucket] ?? "#777080"}
                key={game.game_id}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

