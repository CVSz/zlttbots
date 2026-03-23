import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import pino from "pino";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.API_GATEWAY_PORT ?? "3000");

const coreTarget = process.env.PLATFORM_CORE_URL ?? "http://platform-core:4000";
const workerAiTarget = process.env.WORKER_AI_URL ?? "http://worker-ai:5000";

const app = express();

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
  logger.info({ port, coreTarget, workerAiTarget }, "api-gateway started");
});
