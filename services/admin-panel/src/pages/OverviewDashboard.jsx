import React from "react"

export default function OverviewDashboard({ users, rentUnits }) {
  const totalRevenue = rentUnits.reduce((sum, unit) => sum + unit.monthlyRent, 0)
  const overdueCount = rentUnits.filter((unit) => unit.status === "overdue").length
  const activeUsers = users.filter((u) => u.status === "active").length
  const paidUnits = rentUnits.filter((unit) => unit.status === "paid").length

  return (
    <section className="panel">
      <div className="title-row">
        <h3>Overview Dashboard</h3>
        <p className="muted-text">Platform-wide operational snapshot.</p>
      </div>

      <div className="grid-3">
        <article className="metric-card">
          <span>Total Users</span>
          <h4>{users.length}</h4>
        </article>
        <article className="metric-card">
          <span>Active Users</span>
          <h4>{activeUsers}</h4>
        </article>
        <article className="metric-card">
          <span>Monthly Rent Revenue</span>
          <h4>${totalRevenue}</h4>
        </article>
      </div>

      <div className="grid-2">
        <article className="soft-card">
          <h4>Collection Progress</h4>
          <p>
            {paidUnits} / {rentUnits.length} units marked as paid this month.
          </p>
        </article>
        <article className="soft-card">
          <h4>Risk Alert</h4>
          <p>{overdueCount > 0 ? `${overdueCount} overdue units need follow-up.` : "No overdue units right now."}</p>
        </article>
      </div>
    </section>
  )
}
