import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  buildSeasonWeeks,
  groupSeasonWeeks,
  SeasonCalendar,
} from "../components/season-calendar";
import type { PerformanceGame, PerformanceResponse } from "../lib/types";

function game(
  gameId: string,
  date: string,
  value: number,
): PerformanceGame {
  return {
    game_id: gameId,
    date,
    team: "LVA",
    opponent: "PHO",
    is_home: true,
    played: true,
    minutes: 30,
    result: "W 88–80",
    value,
    average: 20,
    delta: value - 20,
    z_score: 0.5,
    comparison_bucket: value >= 20 ? "above" : "below",
    comparison_label: value >= 20 ? "Above average" : "Below average",
  };
}

const performance: PerformanceResponse = {
  player: {
    id: "player-1",
    display_name: "A'ja Wilson",
    team: { id: "team-1", name: "Las Vegas Aces", abbreviation: "LVA" },
  },
  season: 2024,
  stat: {
    key: "pts",
    label: "Points",
    short_label: "PTS",
    unit: "count",
    precision: 1,
    comparison_direction: "higher_better",
  },
  summary: {
    games_played: 3,
    valid_samples: 3,
    average: 21,
    standard_deviation: 4,
    total: 63,
    high: 23,
    low: 16,
  },
  games: [
    game("game-1", "2024-05-13", 16),
    game("game-2", "2024-05-15", 23),
    game("game-3", "2024-05-20", 24),
  ],
};

describe("buildSeasonWeeks", () => {
  it("groups games into Monday through Sunday weeks and fills rest days", () => {
    const weeks = buildSeasonWeeks([
      game("sunday", "2024-05-19", 18),
      game("monday", "2024-05-20", 22),
    ]);

    expect(weeks).toHaveLength(2);
    expect(weeks[0].id).toBe("2024-05-13");
    expect(weeks[0].days).toHaveLength(7);
    expect(weeks[0].days[6].game?.game_id).toBe("sunday");
    expect(weeks[1].days[0].game?.game_id).toBe("monday");
  });

  it("groups consecutive season weeks into sets of four", () => {
    const weeks = buildSeasonWeeks([
      game("week-1", "2024-05-13", 18),
      game("week-2", "2024-05-20", 22),
      game("week-3", "2024-05-27", 20),
      game("week-4", "2024-06-03", 24),
      game("week-5", "2024-06-10", 26),
    ]);
    const groups = groupSeasonWeeks(weeks);

    expect(groups).toHaveLength(2);
    expect(groups[0].startWeekNumber).toBe(1);
    expect(groups[0].endWeekNumber).toBe(4);
    expect(groups[0].weeks).toHaveLength(4);
    expect(groups[1].startWeekNumber).toBe(5);
    expect(groups[1].endWeekNumber).toBe(5);
    expect(groups[1].weeks).toHaveLength(1);
  });
});

describe("SeasonCalendar", () => {
  it("shows every played week and removes week navigation", () => {
    render(<SeasonCalendar performance={performance} />);

    expect(screen.getByRole("heading", { name: "Points by week" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "May 13 – May 19, 2024" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "May 20 – May 26, 2024" })).toBeInTheDocument();
    expect(screen.getAllByText("PTS")).toHaveLength(3);
    expect(screen.getAllByText("24.0")).toHaveLength(1);
    expect(screen.queryByText("Rebounds")).not.toBeInTheDocument();
    expect(screen.queryByText("Game complete")).not.toBeInTheDocument();
    expect(screen.queryByText("Below average")).not.toBeInTheDocument();
    expect(screen.queryByText("Above average")).not.toBeInTheDocument();
    expect(screen.queryByText("Week average")).not.toBeInTheDocument();
    expect(screen.queryByText("Week high")).not.toBeInTheDocument();
    expect(screen.queryByText("From season avg")).not.toBeInTheDocument();
    expect(screen.queryByText("Week 1")).not.toBeInTheDocument();
    expect(screen.queryByText("Week 2")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Previous week" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Next week" })).not.toBeInTheDocument();
    expect(screen.getAllByText("Rest day")).toHaveLength(11);
  });

  it("renders a separate card for each four-week group", () => {
    const groupedPerformance = {
      ...performance,
      games: [
        game("week-1", "2024-05-13", 18),
        game("week-2", "2024-05-20", 22),
        game("week-3", "2024-05-27", 20),
        game("week-4", "2024-06-03", 24),
        game("week-5", "2024-06-10", 26),
      ],
    };
    const { container } = render(
      <SeasonCalendar performance={groupedPerformance} />,
    );
    const groupCards = container.querySelectorAll(".calendar-period-group");

    expect(groupCards).toHaveLength(2);
    expect(groupCards[0].querySelectorAll(".calendar-week-block")).toHaveLength(4);
    expect(groupCards[1].querySelectorAll(".calendar-week-block")).toHaveLength(1);
    expect(
      screen.getByRole("heading", {
        name: "Weeks 1–4 May 13 – Jun 9, 2024",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Week 5 Jun 10 – Jun 16, 2024",
      }),
    ).toBeInTheDocument();
  });
});
