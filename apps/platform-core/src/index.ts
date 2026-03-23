import express from "express";
import { Kafka } from "kafkajs";
import pino from "pino";
import { z } from "zod";
import crypto from "node:crypto";
import { Pool } from "pg";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.PLATFORM_CORE_PORT ?? "4000");
const kafkaBrokers = (process.env.KAFKA_BROKERS ?? "kafka:9092")
  .split(",")
  .map((broker) => broker.trim())
  .filter(Boolean);

if (kafkaBrokers.length === 0) {
  throw new Error("KAFKA_BROKERS must include at least one broker");
}

const deployPayloadSchema = z.object({
  projectId: z.string().min(1).max(128),
  branch: z.string().min(1).max(128).optional(),
  actor: z.string().min(1).max(128).optional(),
});

const databaseUrl = process.env.DATABASE_URL;
const dbPool = databaseUrl
  ? new Pool({
      connectionString: databaseUrl,
      max: Number(process.env.DB_POOL_MAX ?? "10"),
      idleTimeoutMillis: Number(process.env.DB_IDLE_TIMEOUT_MS ?? "30000"),
      ssl: process.env.DB_SSL_MODE === "require" ? { rejectUnauthorized: false } : undefined,
    })
  : null;

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "1mb" }));

app.use((req, res, next) => {
  const requestId = req.header("x-request-id") ?? crypto.randomUUID();
  res.setHeader("x-request-id", requestId);
  req.headers["x-request-id"] = requestId;
  next();
});

const kafka = new Kafka({ brokers: kafkaBrokers });
const producer = kafka.producer();

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "platform-core", database: Boolean(dbPool) });
});

app.post("/deploy", async (req, res) => {
  const parsed = deployPayloadSchema.safeParse(req.body);
  const requestId = req.header("x-request-id") ?? crypto.randomUUID();

  if (!parsed.success) {
    logger.warn({ requestId, details: parsed.error.flatten() }, "deploy.invalid_payload");
    return res.status(400).json({
      ok: false,
      error: "Invalid request payload",
      details: parsed.error.flatten(),
    });
  }

  const deployId = crypto.randomUUID();

  await producer.send({
    topic: process.env.DEPLOY_TOPIC ?? "deploy.started",
    messages: [{ value: JSON.stringify({ deployId, ...parsed.data, requestId }) }],
  });

  if (dbPool) {
    await dbPool.query(
      `INSERT INTO deployments (id, project_id, status, url)
       VALUES ($1, $2, $3, $4)`,
      [deployId, parsed.data.projectId, "QUEUED", null],
    );
  }

  logger.info(
    {
      service: "platform-core",
      event: "deploy.started",
      requestId,
      deployId,
      projectId: parsed.data.projectId,
      timestamp: Date.now(),
    },
    "deploy.started",
  );

  return res.status(202).json({ ok: true, status: "QUEUED", deployId });
});

async function initDatabase() {
  if (!dbPool) {
    logger.warn("DATABASE_URL is not configured; deployment persistence is disabled");
    return;
  }

  await dbPool.query(`
    CREATE TABLE IF NOT EXISTS deployments (
      id UUID PRIMARY KEY,
      project_id TEXT NOT NULL,
      status TEXT NOT NULL,
      url TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);
}

async function start() {
  try {
    await producer.connect();
    await initDatabase();

    const server = app.listen(port, () => {
      logger.info({ port, kafkaBrokers }, "platform-core.started");
    });

    const shutdown = async (signal: string) => {
      logger.info({ signal }, "platform-core.shutdown");
      await producer.disconnect();
      if (dbPool) {
        await dbPool.end();
      }
      server.close(() => process.exit(0));
    };

    process.on("SIGTERM", () => {
      void shutdown("SIGTERM");
    });
    process.on("SIGINT", () => {
      void shutdown("SIGINT");
    });
  } catch (error) {
    logger.error({ error }, "Failed to start platform-core");
    process.exit(1);
  }
}

void start();
