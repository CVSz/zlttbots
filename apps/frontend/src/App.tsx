import { useEffect, useState } from "react";
import Landing from "./Landing";
import Logs from "./Logs";

type LoginResponse = { ok: boolean; token?: string; error?: string; userId?: string };
type DeployResponse = { ok: boolean; status?: string; error?: string; deploy?: { url: string } };
type GalleryResponse = { ok: boolean; projects?: Array<{ projectId: string; url: string }> };

export default function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [project, setProject] = useState("");
  const [repo, setRepo] = useState("");
  const [status, setStatus] = useState("Idle");
  const [isDeploying, setIsDeploying] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token") ?? "");
  const [gallery, setGallery] = useState<Array<{ projectId: string; url: string }>>([]);

  const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  const register = async () => {
    if (!email.trim() || !password) {
      setStatus("Registration requires both email and password.");
      return;
    }

    const res = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim(), password }),
    });
    setStatus(res.ok ? "Registered. Now login." : "Registration failed.");
  };

  const login = async () => {
    if (!email.trim() || !password) {
      setStatus("Login requires both email and password.");
      return;
    }

    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim(), password }),
    });
    const data = (await res.json()) as LoginResponse;

    if (!res.ok || !data.ok || !data.token) {
      setStatus(data.error ?? "Login failed");
      return;
    }

    localStorage.setItem("token", data.token);
    setToken(data.token);
    setStatus("Logged in");
  };

  const deploy = async () => {
    setIsDeploying(true);
    try {
      const res = await fetch("/core/deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ projectId: project.trim() }),
      });
      const data = (await res.json()) as DeployResponse;
      setStatus(data.ok ? `Deploy queued: ${data.deploy?.url ?? data.status}` : (data.error ?? "Deploy failed"));
    } finally {
      setIsDeploying(false);
    }
  };

  const deployRepo = async () => {
    const res = await fetch("/core/deploy/github", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders },
      body: JSON.stringify({ repo: repo.trim() }),
    });
    const data = (await res.json()) as DeployResponse;
    setStatus(data.ok ? (data.status ?? "GitHub build started") : (data.error ?? "GitHub deploy failed"));
  };

  const loadGallery = async () => {
    const res = await fetch("/core/projects/public", { headers: { ...authHeaders } });
    const data = (await res.json()) as GalleryResponse;
    setGallery(data.projects ?? []);
  };

  useEffect(() => {
    if (token) {
      void loadGallery();
    }
  }, [token]);

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif", maxWidth: 840, margin: "0 auto" }}>
      <Landing onStartFree={() => setShowSignup(true)} />

      <section
        style={{
          marginTop: "1.5rem",
          background: "#f9fafb",
          borderRadius: "12px",
          padding: "1rem",
          border: "1px solid #e5e7eb",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Live AI Demo</h2>
        <p style={{ marginBottom: 0 }}>❌ Build failed → 🤖 AI analyzing... → ✅ Fixed & deployed</p>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2 style={{ fontSize: "1.3rem" }}>Authentication</h2>
        {showSignup ? <p style={{ color: "#111827" }}>Signup step simulated. Connect GitHub, then deploy your first app.</p> : null}

        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          type="password"
        />
        <button onClick={register}>Register</button>
        <button onClick={login}>Login</button>

        <h2>Deploy Project</h2>
        <input value={project} onChange={(e) => setProject(e.target.value)} placeholder="Project ID" />
        <button onClick={deploy} disabled={isDeploying}>
          {isDeploying ? "Deploying..." : "Deploy"}
        </button>

        <h2>1-Click GitHub Deploy</h2>
        <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="https://github.com/org/repo" />
        <button onClick={deployRepo}>Deploy Repo</button>

        <h2>Public Gallery</h2>
        <button onClick={loadGallery}>Refresh Gallery</button>
        <ul>
          {gallery.map((projectItem) => (
            <li key={projectItem.projectId}>
              <a href={projectItem.url} target="_blank" rel="noreferrer">
                {projectItem.projectId}
              </a>
            </li>
          ))}
        </ul>

        <h2>Live Logs</h2>
        <Logs />

        <div style={{ marginTop: "1rem" }}>
          <strong>Status:</strong> {status}
        </div>
      </section>
    </div>
  );
}
