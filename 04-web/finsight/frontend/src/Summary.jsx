export default function Summary({ summary, fileName, totalRows }) {
  return (
    <div
      className="fade-in"
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(233,69,96,0.3)",
        borderRadius: 16,
        padding: "20px 24px",
        backdropFilter: "blur(12px)",
        boxShadow: "0 0 30px rgba(233,69,96,0.08)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 6, height: 6, borderRadius: "50%",
            background: "#e94560", boxShadow: "0 0 8px #e94560",
          }} />
          <span style={{ color: "#e94560", fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1.5 }}>
            AI Саммари
          </span>
        </div>
        {fileName && (
          <span style={{ color: "#444", fontSize: 12 }}>
            {fileName} · {totalRows} строк
          </span>
        )}
      </div>
      <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.9, color: "#d0d0d0" }}>{summary}</p>
    </div>
  );
}
