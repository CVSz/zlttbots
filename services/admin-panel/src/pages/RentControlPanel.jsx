import React, { useState } from "react"

export default function RentControlPanel({ rentUnits, onAddRentUnit, onUpdateRentStatus }) {
  const [form, setForm] = useState({ id: "", tenant: "", monthlyRent: 0, dueDate: "", status: "pending" })

  function handleSubmit(event) {
    event.preventDefault()
    onAddRentUnit({ ...form, monthlyRent: Number(form.monthlyRent) })
    setForm({ id: "", tenant: "", monthlyRent: 0, dueDate: "", status: "pending" })
  }

  return (
    <section className="panel">
      <h3>Rent Control Panel</h3>

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
          {rentUnits.map((unit) => (
            <tr key={unit.id}>
              <td>{unit.id}</td>
              <td>{unit.tenant}</td>
              <td>${unit.monthlyRent}</td>
              <td>{unit.dueDate}</td>
              <td>{unit.status}</td>
              <td className="button-group">
                {['paid', 'pending', 'overdue'].map((status) => (
                  <button type="button" key={status} onClick={() => onUpdateRentStatus(unit.id, status)}>
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
