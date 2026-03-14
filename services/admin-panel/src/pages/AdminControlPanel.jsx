import React, { useMemo, useState } from "react"

export default function AdminControlPanel({
  users,
  settings,
  billingRecords,
  onUpdateSettings,
  onAddUser,
  onToggleUserStatus,
  onUpdateBillingStatus
}) {
  const [form, setForm] = useState({ name: "", email: "", role: "user" })

  const enrichedBillingRecords = useMemo(
    () =>
      billingRecords.map((record) => ({
        ...record,
        userName: users.find((user) => user.id === record.userId)?.name ?? "Unknown User"
      })),
    [billingRecords, users]
  )

  const totalDue = enrichedBillingRecords
    .filter((record) => record.status !== "paid")
    .reduce((sum, record) => sum + record.amount, 0)

  function handleSubmit(event) {
    event.preventDefault()
    onAddUser(form)
    setForm({ name: "", email: "", role: "user" })
  }

  return (
    <section className="panel">
      <h3>Admin Control Panel</h3>

      <div className="grid-2">
        <article>
          <h4>System Settings</h4>
          <label>
            <input
              type="checkbox"
              checked={settings.maintenanceMode}
              onChange={(event) => onUpdateSettings("maintenanceMode", event.target.checked)}
            />
            Maintenance Mode
          </label>
          <label>
            <input
              type="checkbox"
              checked={settings.autoApprovalForUsers}
              onChange={(event) => onUpdateSettings("autoApprovalForUsers", event.target.checked)}
            />
            Auto-approve New Users
          </label>
          <label>
            <input
              type="checkbox"
              checked={settings.billingAlerts}
              onChange={(event) => onUpdateSettings("billingAlerts", event.target.checked)}
            />
            Billing Alerts
          </label>
          <label>
            Max Concurrent Sessions
            <input
              type="number"
              value={settings.maxConcurrentSessions}
              min="1"
              onChange={(event) => onUpdateSettings("maxConcurrentSessions", Number(event.target.value))}
            />
          </label>
        </article>

        <article>
          <h4>Create User</h4>
          <form onSubmit={handleSubmit} className="stacked-form">
            <input
              placeholder="Full name"
              value={form.name}
              onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
              required
            />
            <input
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
              required
            />
            <select
              value={form.role}
              onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
            <button type="submit">Add User</button>
          </form>
        </article>
      </div>

      <h4>User Access Controls</h4>
      <ul className="list-reset">
        {users.map((user) => (
          <li key={user.id} className="row-between">
            <span>
              {user.name} ({user.role}) <span className={`pill ${user.status}`}>{user.status}</span>
            </span>
            <button type="button" onClick={() => onToggleUserStatus(user.id)}>
              {user.status === "active" ? "Suspend" : "Activate"}
            </button>
          </li>
        ))}
      </ul>

      <div className="title-row" style={{ marginTop: "1.2rem" }}>
        <h4>User Billing & Payments</h4>
        <p className="muted-text">Outstanding balance: ${totalDue.toFixed(2)}</p>
      </div>
      <table>
        <thead>
          <tr>
            <th>Invoice</th>
            <th>User</th>
            <th>Plan</th>
            <th>Amount</th>
            <th>Due Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {enrichedBillingRecords.map((record) => (
            <tr key={record.id}>
              <td>{record.id}</td>
              <td>{record.userName}</td>
              <td>{record.plan}</td>
              <td>${record.amount.toFixed(2)}</td>
              <td>{record.dueDate}</td>
              <td>
                <span className={`pill ${record.status}`}>{record.status}</span>
              </td>
              <td>
                <div className="button-group">
                  <button type="button" onClick={() => onUpdateBillingStatus(record.id, "paid")}>Paid</button>
                  <button
                    type="button"
                    className="ghost"
                    onClick={() => onUpdateBillingStatus(record.id, "pending")}
                  >
                    Pending
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => onUpdateBillingStatus(record.id, "overdue")}
                  >
                    Overdue
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
