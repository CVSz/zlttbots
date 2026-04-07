import { describe, expect, it } from "vitest";
import { calculateMomentum, optimizeCaption, rankProducts } from "./engine.js";

describe("affiliate engine", () => {
  it("calculates deterministic momentum", () => {
    const score = calculateMomentum({
      productId: "p1",
      category: "tech",
      impressions: 1000,
      clicks: 120,
      conversions: 24,
    });

    expect(score).toBe(0.156);
  });

  it("sorts products by momentum descending", () => {
    const ranked = rankProducts([
      { productId: "a", category: "x", impressions: 100, clicks: 10, conversions: 2 },
      { productId: "b", category: "x", impressions: 100, clicks: 20, conversions: 8 },
    ]);

    expect(ranked[0]?.productId).toBe("b");
  });

  it("optimizes caption using deterministic directives", () => {
    const output = optimizeCaption({
      currentCaption: "สินค้าใช้ง่าย",
      feedback: ["weak_cta", "not_clear"],
      audience: "มือใหม่",
    });

    expect(output).toContain("ปิดท้ายด้วยคำชวนลงมือทำ");
    expect(output).toContain("ชี้ประโยชน์หลักให้ชัด");
  });
});
