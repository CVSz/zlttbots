import React from "react"

const links = [
  { key: "overview", label: "Overview Dashboard" },
  { key: "user", label: "User Dashboard" },
  { key: "admin", label: "Admin Dashboard" },
  { key: "admin-control", label: "Admin Control Panel" },
  { key: "rent-control", label: "Rent Control Panel" }
]

export default function Navigation({ activePage, onNavigate, onLogout, currentUser }) {
  return (
    <header className="top-nav panel">
      <div>
        <h2>zTTato Platform</h2>
        <p>
          Signed in as <strong>{currentUser.name}</strong> ({currentUser.role})
        </p>
      </div>
      <nav>
        {links.map((item) => (
          <button
            type="button"
            key={item.key}
            className={activePage === item.key ? "active" : ""}
            onClick={() => onNavigate(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <button type="button" className="secondary" onClick={onLogout}>
        Logout
      </button>
    </header>
  )
}
