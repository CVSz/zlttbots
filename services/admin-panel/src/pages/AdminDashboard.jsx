import React from "react"

export default function AdminDashboard({ users, settings }) {
  const suspendedUsers = users.filter((user) => user.status === "suspended").length

  return (
    <section className="panel">
      <h3>Admin Dashboard</h3>
      <div className="grid-3">
        <article className="metric-card">
          <span>Total Accounts</span>
          <h4>{users.length}</h4>
        </article>
        <article className="metric-card">
          <span>Suspended Accounts</span>
          <h4>{suspendedUsers}</h4>
        </article>
        <article className="metric-card">
          <span>Maintenance Mode</span>
          <h4>{settings.maintenanceMode ? "ON" : "OFF"}</h4>
        </article>
      </div>
      <h4>User Directory</h4>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>{user.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
