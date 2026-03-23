import express from "express";
import { Kafka } from "kafkajs";
import pino from "pino";
import { z } from "zod";
import crypto from "node:crypto";
import { Pool } from "pg";
import { checkLimits } from "./limits.js";
import { createOrg, addMember, getOrg, requireRole } from "./org.js";
import { generatePublicUrl } from "./public.js";
import { getRepos } from "./github.js";

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
  repo: z.string().min(1).max(500).optional(),
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

const githubDeploySchema = z.object({
  repo: z.string().min(1).max(500),
});

const createOrgSchema = z.object({
  name: z.string().min(1).max(120),
});

const addMemberSchema = z.object({
  userId: z.string().min(1).max(128),
  role: z.enum(["ADMIN", "MEMBER"]).default("MEMBER"),
});

type DeployRecord = {
  projectId: string;
  url: string;
  isPublic: boolean;
  createdAt: string;
  tenantId: string;
};

const deployments: DeployRecord[] = [];
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

function requireUserContext(req: express.Request): { userId: string; tenantId: string } {
  const userId = req.header("x-user-id");
  const tenantId = req.header("x-tenant-id");
  if (!userId || !tenantId) {
    throw new Error("Missing user context");
  }
  return { userId, tenantId };
}

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "platform-core", database: Boolean(dbPool) });
});

app.get("/github/repos", async (req, res) => {
  const token = req.header("x-github-token");
  if (!token) {
    return res.status(400).json({ ok: false, error: "x-github-token header required" });
  }

  const repos = await getRepos(token);
  return res.status(200).json({ ok: true, repos });
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
  const { userId, tenantId } = requireUserContext(req);
  const limits = await checkLimits(userId);
  const tenantDeployments = deployments.filter((entry) => entry.tenantId === tenantId).length;
  if (tenantDeployments >= limits.maxDeploys) {
    return res.status(403).json({ ok: false, error: "Deploy limit reached. Upgrade required." });
  }

  await producer.send({
    topic: process.env.DEPLOY_TOPIC ?? "deploy.started",
    messages: [{ value: JSON.stringify({ ...parsed.data, tenantId, userId }) }],
  });

  const record: DeployRecord = {
    projectId: parsed.data.projectId,
    url: generatePublicUrl(parsed.data.projectId),
    isPublic: true,
    createdAt: new Date().toISOString(),
    tenantId,
  };
  deployments.push(record);

  logger.info({ projectId: parsed.data.projectId, tenantId }, "Deployment event published");
  return res.status(202).json({ ok: true, status: "QUEUED", deploy: record });
});

app.post("/deploy/github", async (req, res) => {
  const parsed = githubDeploySchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "Invalid GitHub deploy payload" });
  }

  const { userId, tenantId } = requireUserContext(req);
  await producer.send({
    topic: process.env.DEPLOY_TOPIC ?? "deploy.started",
    messages: [{ value: JSON.stringify({ repo: parsed.data.repo, tenantId, userId }) }],
  });

  logger.info({ repo: parsed.data.repo, tenantId }, "GitHub deployment queued");
  return res.status(202).json({ ok: true, status: "BUILD_STARTED" });
});

app.get("/projects/public", (_req, res) => {
  const publicProjects = deployments.filter((item) => item.isPublic);
  return res.status(200).json({ ok: true, projects: publicProjects });
});

app.post("/orgs", (req, res) => {
  const parsed = createOrgSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "Invalid organization payload" });
  }

  const { userId } = requireUserContext(req);
  const org = createOrg(parsed.data.name, userId);
  return res.status(201).json({ ok: true, org });
});

app.post("/orgs/:orgId/members", (req, res) => {
  const parsed = addMemberSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "Invalid membership payload" });
  }

  const { userId } = requireUserContext(req);
  const org = getOrg(req.params.orgId);
  if (!org) {
    return res.status(404).json({ ok: false, error: "Organization not found" });
  }

  try {
    requireRole(userId, org, ["OWNER", "ADMIN"]);
    const updatedOrg = addMember(req.params.orgId, parsed.data.userId, parsed.data.role);
    return res.status(200).json({ ok: true, org: updatedOrg });
  } catch (error) {
    logger.warn({ error, orgId: req.params.orgId, userId }, "Organization role check failed");
    return res.status(403).json({ ok: false, error: "Forbidden" });
  }
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
