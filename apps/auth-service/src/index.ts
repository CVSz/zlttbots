import argon2 from "argon2";
import express from "express";
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import jwt from "jsonwebtoken";
import pino from "pino";
import { randomUUID } from "node:crypto";
import { z } from "zod";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.AUTH_SERVICE_PORT ?? "3001");
const jwtSecret = process.env.JWT_SECRET;

if (!jwtSecret || jwtSecret.length < 32) {
  throw new Error("JWT_SECRET is required and must be at least 32 characters long");
}

const registerSchema = z.object({
  email: z.string().email().max(320),
  password: z.string().min(12).max(128),
});

const loginSchema = registerSchema;

type User = {
  id: string;
  email: string;
  passwordHash: string;
  tenantId: string;
};

const usersByEmail = new Map<string, User>();

const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(
  rateLimit({
    windowMs: 15 * 60 * 1000,
    max: Number(process.env.AUTH_RATE_LIMIT_MAX ?? "120"),
    standardHeaders: true,
    legacyHeaders: false,
  }),
);
app.use(express.json({ limit: "1mb" }));

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "auth-service" });
});

app.post("/register", async (req, res) => {
  const parsed = registerSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "Invalid registration payload" });
  }

  const email = parsed.data.email.toLowerCase();
  if (usersByEmail.has(email)) {
    return res.status(409).json({ ok: false, error: "Email already registered" });
  }

  const user: User = {
    id: randomUUID(),
    email,
    passwordHash: await argon2.hash(parsed.data.password, { type: argon2.argon2id }),
    tenantId: randomUUID(),
  };

  usersByEmail.set(email, user);
  logger.info({ userId: user.id, tenantId: user.tenantId }, "User registered");
  return res.status(201).json({ ok: true, userId: user.id, tenantId: user.tenantId });
});

app.post("/login", async (req, res) => {
  const parsed = loginSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "Invalid login payload" });
  }

  const email = parsed.data.email.toLowerCase();
  const user = usersByEmail.get(email);
  if (!user) {
    return res.status(401).json({ ok: false, error: "Unauthorized" });
  }

  const verified = await argon2.verify(user.passwordHash, parsed.data.password);
  if (!verified) {
    return res.status(401).json({ ok: false, error: "Unauthorized" });
  }

  const token = jwt.sign({ userId: user.id, tenantId: user.tenantId }, jwtSecret, {
    expiresIn: "1h",
    issuer: "zlttbots-auth-service",
    audience: "zlttbots",
  });

  return res.status(200).json({ ok: true, token, userId: user.id, tenantId: user.tenantId });
});

app.listen(port, () => {
  logger.info({ port }, "auth-service started");
});
