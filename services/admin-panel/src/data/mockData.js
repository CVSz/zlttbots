export const initialUsers = [
  { id: 1, name: "Nina Tran", email: "nina@zttato.com", role: "admin", status: "active" },
  { id: 2, name: "Kai Le", email: "kai@zttato.com", role: "user", status: "active" },
  { id: 3, name: "Mila Do", email: "mila@zttato.com", role: "user", status: "suspended" }
]

export const initialRentUnits = [
  { id: "A-101", tenant: "Thanh Nguyen", monthlyRent: 320, dueDate: "2026-04-01", status: "paid" },
  { id: "A-102", tenant: "Linh Pham", monthlyRent: 340, dueDate: "2026-04-05", status: "overdue" },
  { id: "B-201", tenant: "Quoc Ho", monthlyRent: 295, dueDate: "2026-04-10", status: "pending" }
]

export const initialSystemSettings = {
  maintenanceMode: false,
  autoApprovalForUsers: true,
  billingAlerts: true,
  maxConcurrentSessions: 3
}

export const initialBillingRecords = [
  { id: "INV-1001", userId: 1, plan: "Enterprise", amount: 249, dueDate: "2026-04-02", status: "paid" },
  { id: "INV-1002", userId: 2, plan: "Pro", amount: 79, dueDate: "2026-04-08", status: "pending" },
  { id: "INV-1003", userId: 3, plan: "Starter", amount: 29, dueDate: "2026-03-28", status: "overdue" }
]

export const authUsers = [
  { email: "admin@zttato.com", password: "admin123", role: "admin", name: "Platform Admin" },
  { email: "user@zttato.com", password: "user123", role: "user", name: "Platform User" }
]
