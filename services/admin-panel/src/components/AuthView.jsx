import React, { useState } from "react"

export default function AuthView({ onLogin }) {
  const [credentials, setCredentials] = useState({ email: "", password: "" })
  const [error, setError] = useState("")

  function handleChange(event) {
    const { name, value } = event.target
    setCredentials((prev) => ({ ...prev, [name]: value }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    const ok = onLogin(credentials)
    if (!ok) {
      setError("Invalid credentials. Try admin@zttato.com/admin123 or user@zttato.com/user123")
      return
    }
    setError("")
  }

  return (
    <div className="auth-shell">
      <form className="panel auth-card" onSubmit={handleSubmit}>
        <h1>zTTato Auth</h1>
        <p>Sign in to access dashboards and control panels.</p>
        <label>
          Email
          <input name="email" type="email" value={credentials.email} onChange={handleChange} required />
        </label>
        <label>
          Password
          <input name="password" type="password" value={credentials.password} onChange={handleChange} required />
        </label>
        {error && <p className="error-text">{error}</p>}
        <button type="submit">Sign in</button>
      </form>
    </div>
  )
}
