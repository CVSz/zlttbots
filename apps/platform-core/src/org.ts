import { randomUUID } from "node:crypto";
import type { Org, OrgMember, Role } from "../../../packages/shared-types/org.js";

const orgs = new Map<string, Org>();

export function createOrg(name: string, ownerId: string): Org {
  const ownerMember: OrgMember = { userId: ownerId, role: "OWNER" };
  const org: Org = {
    id: randomUUID(),
    name,
    members: [ownerMember],
  };
  orgs.set(org.id, org);
  return org;
}

export function getOrg(orgId: string): Org | undefined {
  return orgs.get(orgId);
}

export function addMember(orgId: string, userId: string, role: Role = "MEMBER"): Org {
  const org = orgs.get(orgId);
  if (!org) {
    throw new Error("Organization not found");
  }

  if (org.members.some((member) => member.userId === userId)) {
    return org;
  }

  org.members.push({ userId, role });
  return org;
}

export function requireRole(userId: string, org: Org, allowedRoles: Role[]): void {
  const member = org.members.find((entry) => entry.userId === userId);
  if (!member || !allowedRoles.includes(member.role)) {
    throw new Error("Forbidden");
  }
}
