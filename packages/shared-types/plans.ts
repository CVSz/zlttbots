export type PlanName = "FREE" | "PRO";

export interface PlanDefinition {
  name: PlanName;
  maxProjects: number;
  maxDeploys: number;
}

export const Plans: Record<PlanName, PlanDefinition> = {
  FREE: {
    name: "FREE",
    maxProjects: 1,
    maxDeploys: 10,
  },
  PRO: {
    name: "PRO",
    maxProjects: 10,
    maxDeploys: 100,
  },
};
