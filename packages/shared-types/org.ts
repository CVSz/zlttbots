export type Role = "OWNER" | "ADMIN" | "MEMBER";

export interface OrgMember {
  userId: string;
  role: Role;
}

export interface Org {
  id: string;
  name: string;
  members: OrgMember[];
}
