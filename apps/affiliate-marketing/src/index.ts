import express from "express";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import pino from "pino";
import { loadConfig } from "./config.js";
import { generateCaption, optimizeCaption, rankProducts } from "./engine.js";
import { copyRequestSchema, optimizeRequestSchema, trendRequestSchema } from "./schemas.js";

const config = loadConfig(process.env);
const logger = pino({ level: config.LOG_LEVEL });

const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(express.json({ limit: "64kb" }));
app.use(
  rateLimit({
    windowMs: 15 * 60 * 1000,
    max: config.RATE_LIMIT_MAX,
    standardHeaders: true,
    legacyHeaders: false,
  }),
);

app.use((req, res, next) => {
  if (!config.AFFILIATE_API_KEY) {
    return next();
  }

  const apiKey = req.header("x-api-key");
  if (apiKey !== config.AFFILIATE_API_KEY) {
    return res.status(401).json({ ok: false, error: "Unauthorized" });
  }

  return next();
});

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "affiliate-marketing" });
});

app.post("/v1/trends/analyze", (req, res) => {
  const parsed = trendRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: parsed.error.flatten() });
  }

  const rankedProducts = rankProducts(parsed.data.products);
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

app.post("/v1/copy/optimize", (req, res) => {
  const parsed = optimizeRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: parsed.error.flatten() });
  }

  const optimizedCaption = optimizeCaption(parsed.data);
  return res.status(200).json({ ok: true, optimizedCaption });
});

app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  logger.error({ err }, "affiliate-marketing.unhandled_error");
  return res.status(500).json({ ok: false, error: "Internal Server Error" });
});

app.listen(config.AFFILIATE_SERVICE_PORT, () => {
  logger.info({ port: config.AFFILIATE_SERVICE_PORT }, "affiliate-marketing.started");
});
