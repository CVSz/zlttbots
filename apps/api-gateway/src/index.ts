import cors from "cors";
import express, { type Request, type Response } from "express";
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import { createProxyMiddleware } from "http-proxy-middleware";
import pino from "pino";
import crypto from "node:crypto";
import { type IncomingMessage, type ServerResponse } from "node:http";
import { auth } from "./middleware.js";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.API_GATEWAY_PORT ?? "3000");

const allowedOrigins = (process.env.CORS_ALLOWED_ORIGINS ?? "")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);
const routeTargets = {
  "/core": process.env.PLATFORM_CORE_URL ?? "http://platform-core:4000",
  "/ai": process.env.WORKER_AI_URL ?? "http://worker-ai:5000",
  "/auth": process.env.AUTH_SERVICE_URL ?? "http://auth-service:3001",
  "/billing": process.env.BILLING_SERVICE_URL ?? "http://billing-service:3002",
  "/logs": process.env.LOG_SERVICE_URL ?? "http://log-service:6000",
};

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

app.use(auth);

for (const [route, target] of Object.entries(routeTargets)) {
  app.use(
    route,
    createProxyMiddleware({
      target,
      changeOrigin: true,
      pathRewrite: { [`^${route}`]: "" },
      proxyTimeout: Number(process.env.PROXY_TIMEOUT_MS ?? "10000"),
      on: {
        proxyReq: (proxyReq, req: IncomingMessage) => {
          const requestId = req.headers["x-request-id"]?.toString();
          if (requestId) {
            proxyReq.setHeader("x-request-id", requestId);
          }
        },
        error: (err: Error, req: IncomingMessage, res: ServerResponse<IncomingMessage> | NodeJS.WritableStream) => {
          const expressRequest = req as Request;
          const requestId = expressRequest.headers["x-request-id"];
          logger.error(
            { err, requestId, path: expressRequest.url, target },
            "proxy.error",
          );
          const expressResponse = res as Response;
          if (typeof expressResponse.status === "function" && !expressResponse.headersSent) {
            expressResponse.status(502).json({ error: "Bad Gateway", requestId });
          }
        },
      },
    }),
  );
}

app.listen(port, () => {
  logger.info({ port, allowedOrigins, routeTargets }, "api-gateway.started");
});
