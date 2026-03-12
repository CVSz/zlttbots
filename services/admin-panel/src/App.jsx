import React, { useMemo, useState } from "react"

import AuthView from "./components/AuthView.jsx"
import Navigation from "./components/Navigation.jsx"
import AdminControlPanel from "./pages/AdminControlPanel.jsx"
import AdminDashboard from "./pages/AdminDashboard.jsx"
import OverviewDashboard from "./pages/OverviewDashboard.jsx"
import RentControlPanel from "./pages/RentControlPanel.jsx"
import UserDashboard from "./pages/UserDashboard.jsx"
import { authUsers, initialRentUnits, initialSystemSettings, initialUsers } from "./data/mockData.js"

export default function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [activePage, setActivePage] = useState("overview")
  const [users, setUsers] = useState(initialUsers)
  const [rentUnits, setRentUnits] = useState(initialRentUnits)
  const [settings, setSettings] = useState(initialSystemSettings)

  const pageMap = useMemo(
    () => ({
      overview: <OverviewDashboard users={users} rentUnits={rentUnits} />,
      user: <UserDashboard currentUser={currentUser} rentUnits={rentUnits} />,
      admin: <AdminDashboard users={users} settings={settings} />,
      "admin-control": (
        <AdminControlPanel
          users={users}
          settings={settings}
          onUpdateSettings={(key, value) => setSettings((prev) => ({ ...prev, [key]: value }))}
          onAddUser={(newUser) => {
            const id = Math.max(...users.map((user) => user.id), 0) + 1
            setUsers((prev) => [...prev, { ...newUser, id, status: "active" }])
          }}
          onToggleUserStatus={(id) => {
            setUsers((prev) =>
              prev.map((user) =>
                user.id === id
                  ? { ...user, status: user.status === "active" ? "suspended" : "active" }
                  : user
              )
            )
          }}
        />
      ),
      "rent-control": (
        <RentControlPanel
          rentUnits={rentUnits}
          onAddRentUnit={(newUnit) => setRentUnits((prev) => [...prev, newUnit])}
          onUpdateRentStatus={(id, status) => {
            setRentUnits((prev) => prev.map((unit) => (unit.id === id ? { ...unit, status } : unit)))
          }}
        />
      )
    }),
    [currentUser, rentUnits, settings, users]
  )

  function handleLogin(credentials) {
    const matchedUser = authUsers.find(
      (user) => user.email === credentials.email && user.password === credentials.password
    )

    if (!matchedUser) {
      return false
    }

    setCurrentUser(matchedUser)
    return true
  }

  function handleLogout() {
    setCurrentUser(null)
    setActivePage("overview")
  }

  if (!currentUser) {
    return <AuthView onLogin={handleLogin} />
  }

  return (
    <main className="app-shell">
      <Navigation
        activePage={activePage}
        onNavigate={setActivePage}
        onLogout={handleLogout}
        currentUser={currentUser}
      />
      {pageMap[activePage]}
    </main>
  )
}
