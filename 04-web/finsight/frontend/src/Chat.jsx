import { useState, useRef, useEffect } from "react";

export default function Chat({ tableData, history, onNewMessage }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history, table_data: tableData }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ошибка сервера");
      onNewMessage([...history, { user: msg, assistant: data.response }]);
    } catch (e) {
      onNewMessage([...history, { user: msg, assistant: `❌ ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Какая категория самая затратная?",
    "Динамика расходов по месяцам?",
    "Топ-3 статьи расходов?",
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      <div style={{ overflowY: "auto", minHeight: 160, maxHeight: 400, paddingBottom: 8 }}>
        {history.length === 0 && (
          <div>
            <p style={{ color: "#333", textAlign: "center", paddingTop: 20, paddingBottom: 16, fontSize: 13 }}>
              Попробуйте спросить:
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); }}
                  style={{
                    background: "rgba(233,69,96,0.08)",
                    border: "1px solid rgba(233,69,96,0.2)",
                    borderRadius: 20, padding: "6px 14px",
                    color: "#aaa", fontSize: 13, cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => e.target.style.borderColor = "#e94560"}
                  onMouseLeave={(e) => e.target.style.borderColor = "rgba(233,69,96,0.2)"}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {history.map((item, i) => (
          <div key={i} className="fade-in" style={{ marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
              <span style={{
                background: "linear-gradient(135deg, #e94560, #c73652)",
                borderRadius: "14px 14px 3px 14px",
                padding: "9px 16px",
                maxWidth: "72%", fontSize: 14,
                boxShadow: "0 4px 15px rgba(233,69,96,0.25)",
              }}>
                {item.user}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-start", alignItems: "flex-start", gap: 8 }}>
              <div style={{
                width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                background: "linear-gradient(135deg, rgba(233,69,96,0.3), rgba(99,69,233,0.3))",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 14,
              }}>
                ✦
              </div>
              <span style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: "3px 14px 14px 14px",
                padding: "9px 16px",
                maxWidth: "80%", fontSize: 14,
                whiteSpace: "pre-wrap", lineHeight: 1.75,
                color: item.assistant.startsWith("❌") ? "#e94560" : "#d0d0d0",
              }}>
                {item.assistant}
              </span>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 36 }}>
            <span style={{ color: "#444", fontSize: 13, animation: "pulse 1s infinite" }}>
              Claude думает...
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Задайте вопрос по данным..."
          disabled={loading}
          style={{
            flex: 1,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 10, padding: "11px 16px",
            color: "#e0e0e0", fontSize: 14, outline: "none",
            transition: "border-color 0.2s",
          }}
          onFocus={(e) => e.target.style.borderColor = "rgba(233,69,96,0.5)"}
          onBlur={(e) => e.target.style.borderColor = "rgba(255,255,255,0.08)"}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          style={{
            background: input.trim() && !loading
              ? "linear-gradient(135deg, #e94560, #c73652)"
              : "rgba(255,255,255,0.05)",
            border: "none", borderRadius: 10,
            padding: "11px 20px", cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            fontSize: 16, color: "#fff",
            transition: "all 0.2s",
            boxShadow: input.trim() && !loading ? "0 4px 15px rgba(233,69,96,0.3)" : "none",
          }}
        >
          →
        </button>
      </div>
    </div>
  );
}
