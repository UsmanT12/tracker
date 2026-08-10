import { describe, expect, it } from "vitest";

import { formatDelta, formatStatValue } from "../lib/formatting";
import type { StatMetadata } from "../lib/types";

const points: StatMetadata = {
  key: "pts",
  label: "Points",
  short_label: "PTS",
  unit: "count",
  precision: 1,
  comparison_direction: "higher_better",
};

it("formats signed deltas", () => {
  expect(formatDelta(8.6, points)).toBe("+8.6");
  expect(formatDelta(-7.4, points)).toBe("-7.4");
  expect(formatDelta(-0.02, points)).toBe("+0.0");
});

it("formats percentage values and percentage-point deltas", () => {
  const percentage = { ...points, key: "fg_pct", unit: "percentage" as const };
  expect(formatStatValue(52.8, percentage)).toBe("52.8%");
  expect(formatDelta(6.6, percentage)).toBe("+6.6 pp");
});

describe("missing metrics", () => {
  it("uses an em dash", () => {
    expect(formatStatValue(null, points)).toBe("—");
    expect(formatDelta(null, points)).toBe("—");
  });
});
