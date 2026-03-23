import cors from "cors";
import express from "express";
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import { createProxyMiddleware } from "http-proxy-middleware";
import pino from "pino";
import crypto from "node:crypto";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.API_GATEWAY_PORT ?? "3000");

const coreTarget = process.env.PLATFORM_CORE_URL ?? "http://platform-core:4000";
const workerAiTarget = process.env.WORKER_AI_URL ?? "http://worker-ai:5000";
const allowedOrigins = (process.env.CORS_ALLOWED_ORIGINS ?? "")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const app = express();

app.disable("x-powered-by");
app.use(helmet());
app.use(
  rateLimit({
    windowMs: 15 * 60 * 1000,
    max: Number(process.env.RATE_LIMIT_MAX ?? "100"),
    standardHeaders: true,
    legacyHeaders: false,
  }),
);
app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || allowedOrigins.length === 0 || allowedOrigins.includes(origin)) {
        callback(null, true);
        return;
      }

      callback(new Error("CORS origin denied"));
    },
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    credentials: true,
  }),
);

app.use((req, res, next) => {
  const requestId = req.header("x-request-id") ?? crypto.randomUUID();
  res.setHeader("x-request-id", requestId);
  req.headers["x-request-id"] = requestId;
  logger.info({ requestId, path: req.path, method: req.method }, "request.received");
  next();
});

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "api-gateway" });
});

app.use(
  "/core",
  createProxyMiddleware({
    target: coreTarget,
    changeOrigin: true,
    pathRewrite: { "^/core": "" },
  }),
);

app.use(
  "/ai",
  createProxyMiddleware({
    target: workerAiTarget,
    changeOrigin: true,
    pathRewrite: { "^/ai": "" },
  }),
);

app.listen(port, () => {
  logger.info({ port, coreTarget, workerAiTarget, allowedOrigins }, "api-gateway.started");
});
