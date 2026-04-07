import { z } from "zod";

const envSchema = z.object({
  LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"]).default("info"),
  AFFILIATE_SERVICE_PORT: z.coerce.number().int().min(1).max(65535).default(3010),
  RATE_LIMIT_MAX: z.coerce.number().int().min(1).max(5000).default(120),
  AFFILIATE_API_KEY: z.string().min(16).optional(),
});

export type ServiceConfig = z.infer<typeof envSchema>;

export function loadConfig(env: NodeJS.ProcessEnv): ServiceConfig {
  return envSchema.parse(env);
}
