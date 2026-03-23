import express from "express";
import http from "node:http";
import pino from "pino";
import { WebSocket, WebSocketServer } from "ws";
import { z } from "zod";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.LOG_SERVICE_PORT ?? "6000");
const logPostSchema = z.object({
  log: z.string().min(1).max(10_000),
  tenantId: z.string().min(1).max(128).optional(),
});

const app = express();
app.use(express.json({ limit: "1mb" }));
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

const clients = new Set<WebSocket>();

wss.on("connection", (socket) => {
  clients.add(socket as WebSocket);
  logger.info({ activeConnections: clients.size }, "WebSocket client connected");

  socket.on("close", () => {
    clients.delete(socket as WebSocket);
    logger.info({ activeConnections: clients.size }, "WebSocket client disconnected");
  });
});

function broadcastLog(log: string): void {
  for (const socket of clients) {
    if (socket.readyState === socket.OPEN) {
      socket.send(log);
    }
  }
}

app.post("/log", (req, res) => {
  const parsed = logPostSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "Invalid log payload" });
  }

  const payload = parsed.data.tenantId
    ? `[tenant:${parsed.data.tenantId}] ${parsed.data.log}`
    : parsed.data.log;

  broadcastLog(payload);
  logger.info({ messageSize: payload.length }, "Log message broadcast");
  return res.status(202).json({ ok: true });
});

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "log-service" });
});

server.listen(port, () => {
  logger.info({ port }, "log-service started");
});
