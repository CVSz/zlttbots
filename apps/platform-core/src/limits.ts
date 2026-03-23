import axios from "axios";
import { Plans, type PlanDefinition, type PlanName } from "../../../packages/shared-types/plans.js";

export async function checkLimits(userId: string): Promise<PlanDefinition> {
  const billingServiceUrl = process.env.BILLING_SERVICE_URL ?? "http://billing-service:3002";
  const res = await axios.get<{ ok: boolean; plan: PlanName }>(`${billingServiceUrl}/plan/${userId}`);
  return Plans[res.data.plan] ?? Plans.FREE;
}
