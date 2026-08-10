export type ComparisonBucket =
  | "strong_below"
  | "below"
  | "near_average"
  | "above"
  | "strong_above"
  | "dnp"
  | "unavailable";

export interface PlayerListItem {
  id: string;
  display_name: string;
  team_name: string | null;
  team_abbreviation: string | null;
  games_played: number;
  ppg: number | null;
  rpg: number | null;
  apg: number | null;
}

export interface PlayerListResponse {
  items: PlayerListItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface SeasonListResponse {
  seasons: number[];
  default_season: number | null;
}

export interface DataStatus {
  latest_successful_run_at: string | null;
  latest_game_date: string | null;
  players: number;
  games: number;
  player_stat_rows: number;
}

export interface StatMetadata {
  key: string;
  label: string;
  short_label: string;
  unit: "count" | "minutes" | "percentage";
  precision: number;
  comparison_direction: "higher_better" | "lower_better" | "neutral";
}

export interface PerformanceGame {
  game_id: string;
  date: string;
  team: string;
  opponent: string;
  is_home: boolean | null;
  played: boolean;
  minutes: number;
  result: string | null;
  value: number | null;
  average: number | null;
  delta: number | null;
  z_score: number | null;
  comparison_bucket: ComparisonBucket;
  comparison_label: string;
}

export interface PerformanceResponse {
  player: {
    id: string;
    display_name: string;
    team: { id: string; name: string; abbreviation: string | null };
  };
  season: number;
  stat: StatMetadata;
  summary: {
    games_played: number;
    valid_samples: number;
    average: number | null;
    standard_deviation: number | null;
    total: number | null;
    high: number | null;
    low: number | null;
  };
  games: PerformanceGame[];
}

