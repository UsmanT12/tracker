import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

async function requestSeasons() {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ seasons: [2026], default_season: 2026 }),
  });
  vi.stubGlobal("fetch", fetchMock);
  const { getSeasons } = await import("../lib/api");
  await getSeasons();
  return fetchMock;
}

describe("API routing", () => {
  it("uses the app's origin in the browser, even with a private backend binding", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", undefined);
    vi.stubEnv("BACKEND_URL", "https://private-backend.example");
    const fetchMock = await requestSeasons();
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/seasons", { cache: "no-store" });
  });

  it("uses the current deployment's binding during server rendering", async () => {
    vi.stubGlobal("window", undefined);
    vi.stubEnv("BACKEND_URL", "https://preview-backend.example/");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000/api/v1");
    const fetchMock = await requestSeasons();
    expect(fetchMock).toHaveBeenCalledWith(
      "https://preview-backend.example/api/v1/seasons",
      { cache: "no-store" },
    );
  });

  it("connects directly to the local backend when rendering without a binding", async () => {
    vi.stubGlobal("window", undefined);
    vi.stubEnv("BACKEND_URL", undefined);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", undefined);
    const fetchMock = await requestSeasons();
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/v1/seasons", {
      cache: "no-store",
    });
  });

  it.each(["browser", "server"])("supports a separate API URL in the %s", async (runtime) => {
    if (runtime === "server") vi.stubGlobal("window", undefined);
    vi.stubEnv("BACKEND_URL", undefined);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://api.example/api/v1");
    const fetchMock = await requestSeasons();
    expect(fetchMock).toHaveBeenCalledWith("https://api.example/api/v1/seasons", {
      cache: "no-store",
    });
  });
});
