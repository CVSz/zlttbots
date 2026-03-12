import React from "react"

export default function UserDashboard({ currentUser, rentUnits }) {
  const myUnit = rentUnits.find((unit) => unit.tenant.toLowerCase().includes(currentUser.name.split(" ")[0].toLowerCase()))

  return (
    <section className="panel">
      <h3>User Dashboard</h3>
      <p>Welcome back, {currentUser.name}.</p>
      <div className="grid-2">
        <article className="metric-card">
          <span>Role</span>
          <h4>{currentUser.role}</h4>
        </article>
        <article className="metric-card">
          <span>Status</span>
          <h4>Active Session</h4>
        </article>
      </div>
      <h4>Rent Snapshot</h4>
      {myUnit ? (
        <ul>
          <li>Unit: {myUnit.id}</li>
          <li>Monthly Rent: ${myUnit.monthlyRent}</li>
          <li>Due Date: {myUnit.dueDate}</li>
          <li>Status: {myUnit.status}</li>
        </ul>
      ) : (
        <p>No rent unit assigned yet.</p>
      )}
    </section>
  )
}
