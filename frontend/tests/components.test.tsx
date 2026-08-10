import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PerformanceGrid } from "../components/performance-grid";
import { StatSelector } from "../components/stat-selector";
import type { PerformanceGame, StatMetadata } from "../lib/types";

const stat: StatMetadata = {
  key: "pts",
  label: "Points",
  short_label: "PTS",
  unit: "count",
  precision: 1,
  comparison_direction: "higher_better",
};

describe("StatSelector", () => {
  it("requests the selected metric", () => {
    const onChange = vi.fn();
    render(<StatSelector onChange={onChange} value="pts" />);
    fireEvent.click(screen.getByRole("tab", { name: "REB" }));
    expect(onChange).toHaveBeenCalledWith("reb");
  });
});

describe("PerformanceGrid", () => {
  it("shows DNP text without coloring it below average", () => {
    const dnp: PerformanceGame = {
      game_id: "game-1",
      date: "2024-05-14",
      team: "LVA",
      opponent: "PHO",
      is_home: true,
      played: false,
      minutes: 0,
      result: null,
      value: null,
      average: 20,
      delta: null,
      z_score: null,
      comparison_bucket: "dnp",
      comparison_label: "DNP",
    };
    const { container } = render(<PerformanceGrid games={[dnp]} stat={stat} />);
    expect(screen.getAllByText("DNP")).toHaveLength(2);
    expect(container.querySelector(".performance-card")).toHaveClass("dnp");
    expect(container.querySelector(".performance-card")).not.toHaveClass("below");
  });
});

