import type { NextFunction, Request, Response } from "express";
import jwt, { type JwtPayload } from "jsonwebtoken";

type JwtClaims = {
  userId: string;
  tenantId: string;
};

const jwtSecretEnv = process.env.JWT_SECRET;
if (!jwtSecretEnv || jwtSecretEnv.length < 32) {
  throw new Error("JWT_SECRET is required and must be at least 32 characters long");
}

const jwtSecret: string = jwtSecretEnv;
const publicRoutes = new Set(["/healthz", "/auth/login", "/auth/register"]);

function isJwtClaims(value: string | JwtPayload): value is JwtClaims {
  if (typeof value === "string") {
    return false;
  }

  return typeof value.userId === "string" && typeof value.tenantId === "string";
}

export function auth(req: Request, res: Response, next: NextFunction) {
  if (publicRoutes.has(req.path)) {
    return next();
  }

  const authHeader = req.headers.authorization;
  const token = authHeader?.startsWith("Bearer ") ? authHeader.slice(7) : undefined;

  if (!token) {
    return res.status(401).json({ ok: false, error: "Unauthorized" });
  }

  try {
    const decoded = jwt.verify(token, jwtSecret, {
      issuer: "zlttbots-auth-service",
      audience: "zlttbots",
    });

    if (!isJwtClaims(decoded)) {
      return res.status(403).json({ ok: false, error: "Forbidden" });
    }

    req.headers["x-user-id"] = decoded.userId;
    req.headers["x-tenant-id"] = decoded.tenantId;
    return next();
  } catch {
    return res.status(403).json({ ok: false, error: "Forbidden" });
  }
}
