import axios from "axios";
import { Plans, type PlanDefinition, type PlanName } from "../../../packages/shared-types/plans.js";

const BILLING_SERVICE_URL = process.env.BILLING_SERVICE_URL ?? "http://billing-service:3002";
const ALLOWED_BILLING_HOSTS = new Set((process.env.BILLING_ALLOWED_HOSTS ?? "billing-service,localhost").split(",").map((host) => host.trim()).filter(Boolean));

function assertAllowedBillingUrl(rawUrl: string): URL {
  let parsed: URL;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new Error("Invalid billing service URL configuration");
  }

  if (!ALLOWED_BILLING_HOSTS.has(parsed.hostname)) {
    throw new Error("Billing service URL host is not allowed");
  }

  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("Billing service URL protocol is not allowed");
  }

  return parsed;
}

export async function checkLimits(userId: string): Promise<PlanDefinition> {
  const billingBaseUrl = assertAllowedBillingUrl(BILLING_SERVICE_URL);
  const safeUserId = encodeURIComponent(userId.trim());
  const planUrl = new URL(`/plan/${safeUserId}`, billingBaseUrl).toString();
  const res = await axios.get<{ ok: boolean; plan: PlanName }>(planUrl, { timeout: 5000 });
  return Plans[res.data.plan] ?? Plans.FREE;
}
