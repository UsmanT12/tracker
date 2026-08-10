"use client";

import { MoonStar } from "lucide-react";

import { formatDelta, formatStatValue } from "@/lib/formatting";
import type {
  PerformanceGame,
  PerformanceResponse,
  StatMetadata,
} from "@/lib/types";

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export interface CalendarDay {
  date: Date;
  isoDate: string;
  game: PerformanceGame | null;
}

export interface SeasonWeek {
  id: string;
  start: Date;
  end: Date;
  days: CalendarDay[];
}

interface SeasonWeekGroup {
  id: string;
  startWeekNumber: number;
  endWeekNumber: number;
  weeks: SeasonWeek[];
}

function parseDate(value: string): Date {
  return new Date(`${value}T00:00:00Z`);
}

function isoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function startOfWeek(value: Date): Date {
  const result = new Date(value);
  const mondayOffset = (result.getUTCDay() + 6) % 7;
  result.setUTCDate(result.getUTCDate() - mondayOffset);
  return result;
}

function addDays(value: Date, amount: number): Date {
  const result = new Date(value);
  result.setUTCDate(result.getUTCDate() + amount);
  return result;
}

export function buildSeasonWeeks(games: PerformanceGame[]): SeasonWeek[] {
  if (games.length === 0) return [];

  const sortedGames = [...games].sort((a, b) => a.date.localeCompare(b.date));
  const gamesByDate = new Map(sortedGames.map((game) => [game.date, game]));
  const firstMonday = startOfWeek(parseDate(sortedGames[0].date));
  const lastSunday = addDays(
    startOfWeek(parseDate(sortedGames[sortedGames.length - 1].date)),
    6,
  );
  const weeks: SeasonWeek[] = [];

  for (
    let weekStart = firstMonday;
    weekStart <= lastSunday;
    weekStart = addDays(weekStart, 7)
  ) {
    const days = DAY_LABELS.map((_, dayIndex) => {
      const date = addDays(weekStart, dayIndex);
      const dateKey = isoDate(date);
      return {
        date,
        isoDate: dateKey,
        game: gamesByDate.get(dateKey) ?? null,
      };
    });
    weeks.push({
      id: isoDate(weekStart),
      start: weekStart,
      end: days[6].date,
      days,
    });
  }

  return weeks;
}

function formatDateRange(startDate: Date, endDate: Date): string {
  const start = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(startDate);
  const end = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(endDate);
  return `${start} – ${end}`;
}

function formatRange(week: SeasonWeek): string {
  return formatDateRange(week.start, week.end);
}

export function groupSeasonWeeks(
  weeks: SeasonWeek[],
  groupSize = 4,
): SeasonWeekGroup[] {
  const groups: SeasonWeekGroup[] = [];

  for (let groupStart = 0; groupStart < weeks.length; groupStart += groupSize) {
    const groupedWeeks = weeks.slice(groupStart, groupStart + groupSize);
    groups.push({
      id: groupedWeeks[0].id,
      startWeekNumber: groupStart + 1,
      endWeekNumber: groupStart + groupedWeeks.length,
      weeks: groupedWeeks,
    });
  }

  return groups;
}

function formatDay(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(date);
}

function resultClass(result: string | null): string {
  if (result?.trim().startsWith("W")) return "win";
  if (result?.trim().startsWith("L")) return "loss";
  return "";
}

function GameDay({
  day,
  dayIndex,
  featured,
  stat,
}: {
  day: CalendarDay;
  dayIndex: number;
  featured: boolean;
  stat: StatMetadata;
}) {
  const game = day.game;

  return (
    <article
      className={[
        "calendar-day",
        game ? `has-game ${game.comparison_bucket}` : "rest-day",
        featured ? "featured" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <header>
        <span>{DAY_LABELS[dayIndex]}</span>
        <strong>{formatDay(day.date)}</strong>
      </header>
      {game ? (
        <div className="calendar-game">
          <div className="calendar-matchup">
            {game.is_home ? "vs" : "@"} {game.opponent}
          </div>
          {game.result ? (
            <div className={`calendar-result ${resultClass(game.result)}`}>
              {game.result}
            </div>
          ) : null}
          <div className="calendar-stat">
            <span>{stat.short_label}</span>
            <strong>
              {game.played ? formatStatValue(game.value, stat) : "DNP"}
            </strong>
          </div>
          <div className="calendar-comparison">
            <span>{formatDelta(game.delta, stat)}</span>
          </div>
        </div>
      ) : (
        <div className="calendar-rest">
          <span className="calendar-rest-icon">
            <MoonStar aria-hidden="true" size={21} />
          </span>
          <strong>Rest day</strong>
          <span>No game scheduled</span>
        </div>
      )}
    </article>
  );
}

export function SeasonCalendar({
  performance,
}: {
  performance: PerformanceResponse;
}) {
  const weeks = buildSeasonWeeks(performance.games).filter((week) =>
    week.days.some((day) => day.game !== null),
  );
  const weekGroups = groupSeasonWeeks(weeks);

  if (weeks.length === 0) {
    return (
      <section className="panel">
        <div className="empty-state">No games are available for this season.</div>
      </section>
    );
  }

  return (
    <section className="panel calendar-panel">
      <div className="calendar-toolbar">
        <div>
          <p className="eyebrow">Season calendar</p>
          <h2>{performance.stat.label} by week</h2>
          <p>
            One selected stat across every game and rest day of the{" "}
            {performance.season} season.
          </p>
        </div>
        <div className="calendar-season-count">
          <strong>{weeks.length}</strong>
          <span>weeks played</span>
        </div>
      </div>

      <div className="calendar-weeks">
        {weekGroups.map((group) => {
          const groupEnd = group.weeks.at(-1) as SeasonWeek;
          const groupGameCount = group.weeks.reduce(
            (count, week) =>
              count + week.days.filter((day) => day.game !== null).length,
            0,
          );
          const groupLabel =
            group.startWeekNumber === group.endWeekNumber
              ? `Week ${group.startWeekNumber}`
              : `Weeks ${group.startWeekNumber}–${group.endWeekNumber}`;

          return (
            <section
              aria-labelledby={`calendar-group-${group.id}`}
              className="calendar-period-group"
              key={group.id}
            >
              <header className="calendar-period-heading">
                <h3 id={`calendar-group-${group.id}`}>
                  <span>{groupLabel}</span>
                  <strong>
                    {formatDateRange(group.weeks[0].start, groupEnd.end)}
                  </strong>
                </h3>
                <span>
                  {groupGameCount} {groupGameCount === 1 ? "game" : "games"}
                </span>
              </header>
              <div className="calendar-period-weeks">
                {group.weeks.map((week) => {
                  const weekGames = week.days
                    .map((day) => day.game)
                    .filter((game): game is PerformanceGame => game !== null);
                  const featuredGameId = weekGames.at(-1)?.game_id;

                  return (
                    <section
                      aria-labelledby={`calendar-week-${week.id}`}
                      className="calendar-week-block"
                      key={week.id}
                    >
                      <header className="calendar-week-heading">
                        <div>
                          <h4 id={`calendar-week-${week.id}`}>
                            {formatRange(week)}
                          </h4>
                        </div>
                        <span>
                          {weekGames.length}{" "}
                          {weekGames.length === 1 ? "game" : "games"}
                        </span>
                      </header>
                      <div className="season-calendar-scroll">
                        <div className="season-calendar-grid">
                          {week.days.map((day, dayIndex) => (
                            <GameDay
                              day={day}
                              dayIndex={dayIndex}
                              featured={
                                day.game?.game_id === featuredGameId
                              }
                              key={day.isoDate}
                              stat={performance.stat}
                            />
                          ))}
                        </div>
                      </div>
                    </section>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
    </section>
  );
}
