import express from "express";
import OpenAI from "openai";
import pino from "pino";
import { z } from "zod";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.WORKER_AI_PORT ?? "5000");
const requestSchema = z.object({
  logs: z.string().min(1).max(100_000),
});

const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  throw new Error("OPENAI_API_KEY is required");
}

const client = new OpenAI({ apiKey });

const app = express();
app.use(express.json({ limit: "2mb" }));

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "worker-ai" });
});

app.post("/fix", async (req, res) => {
  const parsed = requestSchema.safeParse(req.body);

  if (!parsed.success) {
    return res.status(400).json({
      ok: false,
      error: "Invalid request payload",
      details: parsed.error.flatten(),
    });
  }

  const response = await client.chat.completions.create({
    model: process.env.OPENAI_FIX_MODEL ?? "gpt-4.1-mini",
    temperature: 0,
    messages: [
      {
        role: "system",
        content:
          "You are a software reliability assistant. Return concise remediation steps for the given logs.",
      },
      { role: "user", content: parsed.data.logs },
    ],
  });

  const fix = response.choices[0]?.message?.content?.trim();
  if (!fix) {
    logger.warn("Model returned empty content");
    return res.status(502).json({ ok: false, error: "No remediation output generated" });
  }

  return res.status(200).json({ ok: true, fix });
});

app.listen(port, () => {
  logger.info({ port }, "worker-ai started");
});
