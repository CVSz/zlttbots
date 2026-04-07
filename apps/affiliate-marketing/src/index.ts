import express from "express";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import pino from "pino";
import { z } from "zod";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.AFFILIATE_SERVICE_PORT ?? "3010");

const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(express.json({ limit: "64kb" }));
app.use(
  rateLimit({
    windowMs: 15 * 60 * 1000,
    max: Number(process.env.RATE_LIMIT_MAX ?? "120"),
    standardHeaders: true,
    legacyHeaders: false,
  }),
);

const trendRequestSchema = z.object({
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

const copyRequestSchema = z.object({
  productName: z.string().min(2).max(120),
  audience: z.string().min(2).max(120),
  valueProps: z.array(z.string().min(2).max(120)).min(1).max(5),
  tone: z.enum(["friendly", "expert", "urgent"]).default("friendly"),
});

type TrendProduct = z.infer<typeof trendRequestSchema>["products"][number];

function calculateMomentum(product: TrendProduct): number {
  const ctr = product.impressions === 0 ? 0 : product.clicks / product.impressions;
  const cvr = product.clicks === 0 ? 0 : product.conversions / product.clicks;
  return Number((ctr * 0.55 + cvr * 0.45).toFixed(4));
}

function generateCaption(input: z.infer<typeof copyRequestSchema>): string {
  const highlights = input.valueProps.slice(0, 3).join(" • ");
  if (input.tone === "expert") {
    return `วิเคราะห์แล้วว่า ${input.productName} เหมาะกับ ${input.audience} เพราะ ${highlights}. ถ้าต้องการผลลัพธ์ที่วัดได้ เริ่มทดลองวันนี้และติดตาม KPI แบบรายสัปดาห์.`;
  }

  if (input.tone === "urgent") {
    return `${input.audience} ห้ามพลาด! ${input.productName} จุดเด่นคือ ${highlights}. โปรรอบนี้มีจำกัด รีบเช็กก่อนหมด.`;
  }

  return `${input.productName} สำหรับ ${input.audience} ที่อยากได้ ${highlights}. ใช้ง่าย เห็นผลเร็ว และคุ้มค่าสุด ๆ`;
}

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "affiliate-marketing" });
});

app.post("/v1/trends/analyze", (req, res) => {
  const parsed = trendRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: parsed.error.flatten() });
  }

  const rankedProducts = parsed.data.products
    .map((product) => ({
      ...product,
      momentumScore: calculateMomentum(product),
    }))
    .sort((a, b) => b.momentumScore - a.momentumScore)
    .slice(0, 10);

  return res.status(200).json({ ok: true, rankedProducts });
});

app.post("/v1/copy/generate", (req, res) => {
  const parsed = copyRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: parsed.error.flatten() });
  }

  const caption = generateCaption(parsed.data);
  return res.status(200).json({ ok: true, caption });
});

app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  logger.error({ err }, "affiliate-marketing.unhandled_error");
  return res.status(500).json({ ok: false, error: "Internal Server Error" });
});

app.listen(port, () => {
  logger.info({ port }, "affiliate-marketing.started");
});
