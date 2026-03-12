import React from "react"

export default function OverviewDashboard({ users, rentUnits }) {
  const totalRevenue = rentUnits.reduce((sum, unit) => sum + unit.monthlyRent, 0)
  const overdueCount = rentUnits.filter((unit) => unit.status === "overdue").length
  const activeUsers = users.filter((u) => u.status === "active").length

  return (
    <section className="panel">
      <h3>Overview Dashboard</h3>
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
      <p>Overdue units: {overdueCount}</p>
    </section>
  )
}
