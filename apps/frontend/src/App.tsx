import { useState } from "react";
import Landing from "./Landing";

type DeployResponse = {
  ok: boolean;
  status?: string;
  error?: string;
};

export default function App() {
  const [project, setProject] = useState("");
  const [status, setStatus] = useState("Idle");
  const [isDeploying, setIsDeploying] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const deploy = async () => {
    if (!project.trim()) {
      setStatus("Project ID is required");
      return;
    }

    setIsDeploying(true);
    try {
      const res = await fetch("/core/deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projectId: project.trim() }),
      });

      const data = (await res.json()) as DeployResponse;
      if (!res.ok || !data.ok) {
        setStatus(data.error ?? "Deployment request failed");
        return;
      }

      setStatus(data.status ?? "QUEUED");
    } catch {
      setStatus("Network error while triggering deploy");
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif", maxWidth: 760, margin: "0 auto" }}>
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
        <h2 style={{ fontSize: "1.3rem" }}>Deploy Console</h2>
        {showSignup ? (
          <p style={{ color: "#111827" }}>
            Signup step simulated. Connect GitHub, then deploy your first app.
          </p>
        ) : null}

        <input
          style={{ width: "100%", padding: "0.6rem", marginTop: "1rem" }}
          placeholder="Project ID"
          onChange={(e) => setProject(e.target.value)}
        />

        <button
          style={{ marginTop: "1rem", padding: "0.6rem 1rem" }}
          onClick={deploy}
          disabled={isDeploying}
        >
          {isDeploying ? "Deploying..." : "Deploy"}
        </button>

        <div style={{ marginTop: "1rem" }}>
          <strong>Status:</strong> {status}
        </div>
      </section>
    </div>
  );
}
