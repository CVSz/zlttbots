type LandingProps = {
  onStartFree: () => void;
};

export default function Landing({ onStartFree }: LandingProps) {
  return (
    <section
      style={{
        padding: "3rem 1.5rem",
        textAlign: "center",
        border: "1px solid #e5e7eb",
        borderRadius: "12px",
        background: "#ffffff",
      }}
    >
      <h1 style={{ fontSize: "2rem", margin: 0 }}>Deploy apps in 1 click.</h1>
      <p style={{ marginTop: "1rem", fontSize: "1.1rem", color: "#374151" }}>
        🤖 AI fixes your broken deploys automatically.
      </p>

      <button
        style={{
          marginTop: "1.5rem",
          background: "#111827",
          color: "#ffffff",
          border: "none",
          borderRadius: "8px",
          padding: "0.75rem 1.25rem",
          fontWeight: 600,
          cursor: "pointer",
        }}
        onClick={onStartFree}
      >
        Start Free
      </button>
    </section>
  );
}
