import { useState } from "react";

type DeployResponse = {
  ok: boolean;
  status?: string;
  error?: string;
};

export default function App() {
  const [project, setProject] = useState("");
  const [status, setStatus] = useState("Idle");
  const [isDeploying, setIsDeploying] = useState(false);

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
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif", maxWidth: 680 }}>
      <h1 style={{ fontSize: "1.8rem" }}>ZTTATO Dashboard</h1>
      <p>Deploy your project to the platform orchestration pipeline.</p>

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
    </div>
  );
}
