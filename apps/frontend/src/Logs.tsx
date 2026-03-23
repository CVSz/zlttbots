import { useEffect, useState } from "react";

const wsUrl = import.meta.env.VITE_LOG_WS_URL ?? "ws://localhost:6000";

export default function Logs() {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      setLogs((prev) => [...prev.slice(-199), String(event.data)]);
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ padding: "1rem", background: "#000", color: "#50fa7b", height: "16rem", overflow: "auto" }}>
      {logs.length === 0 ? <div>No logs streamed yet.</div> : null}
      {logs.map((logLine, index) => (
        <div key={`${index}-${logLine.slice(0, 16)}`}>{logLine}</div>
      ))}
    </div>
  );
}
