import express from "express";
import pino from "pino";
import Stripe from "stripe";
import { z } from "zod";
import { Plans, type PlanName } from "../../../packages/shared-types/plans.js";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
const port = Number(process.env.BILLING_SERVICE_PORT ?? "3002");
const stripeSecretKey = process.env.STRIPE_KEY;
const stripeProPriceId = process.env.STRIPE_PRO_PRICE_ID;

if (!stripeSecretKey) {
  throw new Error("STRIPE_KEY is required");
}
if (!stripeProPriceId) {
  throw new Error("STRIPE_PRO_PRICE_ID is required");
}

const stripe = new Stripe(stripeSecretKey);
const checkoutSchema = z.object({
  userId: z.string().min(1).max(128),
});

const userPlans = new Map<string, PlanName>();

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/healthz", (_req, res) => {
  res.status(200).json({ ok: true, service: "billing-service" });
});

app.post("/checkout", async (req, res) => {
  const parsed = checkoutSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: "Invalid checkout payload" });
  }

  const session = await stripe.checkout.sessions.create({
    mode: "subscription",
    payment_method_types: ["card"],
    line_items: [{ price: stripeProPriceId, quantity: 1 }],
    client_reference_id: parsed.data.userId,
    success_url: process.env.BILLING_SUCCESS_URL ?? "http://localhost:5173/success",
    cancel_url: process.env.BILLING_CANCEL_URL ?? "http://localhost:5173/cancel",
  });

  return res.status(200).json({ ok: true, checkoutUrl: session.url });
});

app.post("/webhook", (req, res) => {
  const event = req.body as { type?: string; data?: { object?: { client_reference_id?: string } } };

  if (event.type === "checkout.session.completed") {
    const userId = event.data?.object?.client_reference_id;
    if (userId) {
      userPlans.set(userId, "PRO");
      logger.info({ userId }, "Upgraded user to PRO");
    }
  }

  return res.sendStatus(200);
});

app.get("/plan/:userId", (req, res) => {
  const plan = userPlans.get(req.params.userId) ?? "FREE";
  return res.status(200).json({ ok: true, plan, limits: Plans[plan] });
});

app.listen(port, () => {
  logger.info({ port }, "billing-service started");
});
