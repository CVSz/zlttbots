import { z } from "zod";

export const trendRequestSchema = z.object({
  products: z
    .array(
      z.object({
        productId: z.string().min(1).max(64),
        category: z.string().min(2).max(64),
        impressions: z.number().int().min(0),
        clicks: z.number().int().min(0),
        conversions: z.number().int().min(0),
      }),
    )
    .min(1)
    .max(100),
});

export const copyRequestSchema = z.object({
  productName: z.string().min(2).max(120),
  audience: z.string().min(2).max(120),
  valueProps: z.array(z.string().min(2).max(120)).min(1).max(5),
  tone: z.enum(["friendly", "expert", "urgent"]).default("friendly"),
});

export const optimizeRequestSchema = z.object({
  currentCaption: z.string().min(8).max(512),
  feedback: z.array(z.enum(["too_long", "not_clear", "low_emotion", "weak_cta"])).min(1).max(4),
  audience: z.string().min(2).max(120),
});

export type TrendRequest = z.infer<typeof trendRequestSchema>;
export type TrendProduct = TrendRequest["products"][number];
export type CopyRequest = z.infer<typeof copyRequestSchema>;
export type OptimizeRequest = z.infer<typeof optimizeRequestSchema>;
