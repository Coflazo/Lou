import { describe, expect, it } from "vitest";
import { cn, formatScore, riskToColor, truncate, clamp } from "./utils";

describe("utils", () => {
  it("merges tailwind classes via cn", () => {
    expect(cn("p-2", "p-3")).toBe("p-3");
    expect(cn("bg-paper", null, undefined, "text-ink")).toBe("bg-paper text-ink");
  });

  it("maps risk levels to OKLCH tokens", () => {
    expect(riskToColor("Low")).toBe("var(--color-green)");
    expect(riskToColor("medium")).toBe("var(--color-amber)");
    expect(riskToColor("HIGH")).toBe("var(--color-red)");
    expect(riskToColor(undefined)).toBe("var(--color-warm-gray)");
  });

  it("truncates strings with an ellipsis", () => {
    expect(truncate("short", 100)).toBe("short");
    expect(truncate("a very long string that exceeds the cap", 12)).toMatch(/…$/);
  });

  it("formats scores as percentages with one decimal precision", () => {
    expect(formatScore(0.5)).toBe("50%");
    expect(formatScore(null)).toBe("—");
    expect(formatScore(undefined)).toBe("—");
  });

  it("clamps numbers to the requested bounds", () => {
    expect(clamp(5, 0, 10)).toBe(5);
    expect(clamp(-2, 0, 10)).toBe(0);
    expect(clamp(99, 0, 10)).toBe(10);
  });
});
