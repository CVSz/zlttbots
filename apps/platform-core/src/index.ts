import express from "express";
import { Kafka } from "kafkajs";
import pino from "pino";
import { z } from "zod";

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

const app = express();
app.use(express.json({ limit: "1mb" }));

const kafka = new Kafka({ brokers: kafkaBrokers });
const producer = kafka.producer();

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "platform-core" });
});

app.post("/deploy", async (req, res) => {
  const parsed = deployPayloadSchema.safeParse(req.body);

  if (!parsed.success) {
    return res.status(400).json({
      ok: false,
      error: "Invalid request payload",
      details: parsed.error.flatten(),
    });
  }

  await producer.send({
    topic: process.env.DEPLOY_TOPIC ?? "deploy.started",
    messages: [{ value: JSON.stringify(parsed.data) }],
  });

  logger.info({ projectId: parsed.data.projectId }, "Deployment event published");
  return res.status(202).json({ ok: true, status: "QUEUED" });
});

async function start() {
  try {
    await producer.connect();

    const server = app.listen(port, () => {
      logger.info({ port }, "platform-core started");
    });

    const shutdown = async (signal: string) => {
      logger.info({ signal }, "Shutting down platform-core");
      await producer.disconnect();
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
