import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import pino from "pino";
import { auth } from "./middleware.js";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.API_GATEWAY_PORT ?? "3000");

const coreTarget = process.env.PLATFORM_CORE_URL ?? "http://platform-core:4000";
const workerAiTarget = process.env.WORKER_AI_URL ?? "http://worker-ai:5000";
const authTarget = process.env.AUTH_SERVICE_URL ?? "http://auth-service:3001";
const billingTarget = process.env.BILLING_SERVICE_URL ?? "http://billing-service:3002";
const logTarget = process.env.LOG_SERVICE_URL ?? "http://log-service:6000";

const app = express();

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "api-gateway" });
});

app.use(auth);

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

app.use(
  "/auth",
  createProxyMiddleware({
    target: authTarget,
    changeOrigin: true,
    pathRewrite: { "^/auth": "" },
  }),
);

app.use(
  "/billing",
  createProxyMiddleware({
    target: billingTarget,
    changeOrigin: true,
    pathRewrite: { "^/billing": "" },
  }),
);

app.use(
  "/logs",
  createProxyMiddleware({
    target: logTarget,
    changeOrigin: true,
    pathRewrite: { "^/logs": "" },
  }),
);

app.listen(port, () => {
  logger.info({ port, coreTarget, workerAiTarget, authTarget, billingTarget }, "api-gateway started");
});
