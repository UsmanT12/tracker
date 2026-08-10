import type {
  DataStatus,
  PerformanceResponse,
  PlayerListResponse,
  SeasonListResponse,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getSeasons(): Promise<SeasonListResponse> {
  return apiFetch("/seasons");
}

export function getDataStatus(): Promise<DataStatus> {
  return apiFetch("/data-status");
}

export function getPlayers(options: {
  season?: number;
  search?: string;
  page?: number;
}): Promise<PlayerListResponse> {
  const query = new URLSearchParams();
  if (options.season) query.set("season", String(options.season));
  if (options.search) query.set("search", options.search);
  query.set("page", String(options.page ?? 1));
  query.set("page_size", "24");
  return apiFetch(`/players?${query}`);
}

export function getPerformance(
  playerId: string,
  season: number,
  stat: string,
): Promise<PerformanceResponse> {
  const query = new URLSearchParams({ season: String(season), stat });
  return apiFetch(`/players/${playerId}/performance?${query}`);
}

