import React from "react"

const links = [
  { key: "overview", label: "Overview" },
  { key: "user", label: "User" },
  { key: "admin", label: "Admin" },
  { key: "admin-control", label: "Access Control" },
  { key: "rent-control", label: "Rent Ops" }
]

export default function Navigation({ activePage, onNavigate, onLogout, currentUser }) {
  return (
    <header className="top-nav panel">
      <div className="brand-block">
        <p className="eyebrow">zTTato Platform</p>
        <h2>Operations Workspace</h2>
        <p className="muted-text">
          Signed in as <strong>{currentUser.name}</strong> · {currentUser.role}
        </p>
      </div>

      <nav className="tab-nav" aria-label="Main navigation">
        {links.map((item) => (
          <button
            type="button"
            key={item.key}
            className={activePage === item.key ? "active" : "ghost"}
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
