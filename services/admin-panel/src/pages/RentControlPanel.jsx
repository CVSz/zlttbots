import React, { useMemo, useState } from "react"

export default function RentControlPanel({ rentUnits, onAddRentUnit, onUpdateRentStatus }) {
  const [form, setForm] = useState({ id: "", tenant: "", monthlyRent: 0, dueDate: "", status: "pending" })
  const [statusFilter, setStatusFilter] = useState("all")

  function handleSubmit(event) {
    event.preventDefault()
    onAddRentUnit({ ...form, monthlyRent: Number(form.monthlyRent) })
    setForm({ id: "", tenant: "", monthlyRent: 0, dueDate: "", status: "pending" })
  }

  const visibleUnits = useMemo(() => {
    return rentUnits.filter((unit) => statusFilter === "all" || unit.status === statusFilter)
  }, [rentUnits, statusFilter])

  return (
    <section className="panel">
      <div className="title-row">
        <h3>Rent Control Panel</h3>
        <p className="muted-text">Create, monitor, and resolve rental payment statuses quickly.</p>
      </div>

      <form onSubmit={handleSubmit} className="grid-5">
        <input
          required
          placeholder="Unit ID"
          value={form.id}
          onChange={(event) => setForm((prev) => ({ ...prev, id: event.target.value }))}
        />
        <input
          required
          placeholder="Tenant"
          value={form.tenant}
          onChange={(event) => setForm((prev) => ({ ...prev, tenant: event.target.value }))}
        />
        <input
          required
          type="number"
          min="0"
          placeholder="Monthly Rent"
          value={form.monthlyRent}
          onChange={(event) => setForm((prev) => ({ ...prev, monthlyRent: event.target.value }))}
        />
        <input
          required
          type="date"
          value={form.dueDate}
          onChange={(event) => setForm((prev) => ({ ...prev, dueDate: event.target.value }))}
        />
        <button type="submit">Add Unit</button>
      </form>

      <div className="toolbar">
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="all">All payment statuses</option>
          <option value="paid">Paid</option>
          <option value="pending">Pending</option>
          <option value="overdue">Overdue</option>
        </select>
      </div>

      <table>
        <thead>
          <tr>
            <th>Unit</th>
            <th>Tenant</th>
            <th>Rent</th>
            <th>Due Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {visibleUnits.map((unit) => (
            <tr key={unit.id}>
              <td>{unit.id}</td>
              <td>{unit.tenant}</td>
              <td>${unit.monthlyRent}</td>
              <td>{unit.dueDate}</td>
              <td>
                <span className={`pill ${unit.status}`}>{unit.status}</span>
              </td>
              <td className="button-group">
                {["paid", "pending", "overdue"].map((status) => (
                  <button type="button" className="ghost" key={status} onClick={() => onUpdateRentStatus(unit.id, status)}>
                    {status}
                  </button>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
