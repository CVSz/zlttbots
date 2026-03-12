import React, { useMemo, useState } from "react"

export default function AdminDashboard({ users, settings }) {
  const [query, setQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")

  const suspendedUsers = users.filter((user) => user.status === "suspended").length

  const filteredUsers = useMemo(() => {
    return users.filter((user) => {
      const matchesQuery = [user.name, user.email, user.role]
        .join(" ")
        .toLowerCase()
        .includes(query.toLowerCase())
      const matchesStatus = statusFilter === "all" || user.status === statusFilter
      return matchesQuery && matchesStatus
    })
  }, [query, statusFilter, users])

  return (
    <section className="panel">
      <div className="title-row">
        <h3>Admin Dashboard</h3>
        <p className="muted-text">Live account health and user directory controls.</p>
      </div>

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

      <div className="toolbar">
        <input
          type="search"
          placeholder="Search users by name, email, or role"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
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
          {filteredUsers.map((user) => (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                <span className={`pill ${user.status}`}>{user.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
