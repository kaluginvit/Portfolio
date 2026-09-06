import { useState } from "react";
import FileUpload from "./FileUpload.jsx";
import Summary from "./Summary.jsx";
import Chat from "./Chat.jsx";

export default function App() {
  const [tableData, setTableData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [preview, setPreview] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [totalRows, setTotalRows] = useState(null);
  const [history, setHistory] = useState([]);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (formData, name) => {
    setUploadLoading(true);
    setError(null);
    setHistory([]);
    setTableData(null);
    setSummary(null);

    try {
      const res = await fetch("/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ошибка загрузки");
      setTableData(data.table_data);
      setSummary(data.summary);
      setPreview(data.preview);
      setFileName(name);
      setTotalRows(data.total_rows);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", padding: "40px 16px 60px" }}>
      <div style={{ maxWidth: 820, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <h1 style={{
            fontSize: 32, fontWeight: 700, letterSpacing: -0.5,
            background: "linear-gradient(135deg, #fff 30%, #e94560)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            marginBottom: 8,
          }}>
            ФинАналитик
          </h1>
          <p style={{ color: "#555", fontSize: 14 }}>
            Загрузи CSV или Excel — получи AI-анализ и задавай вопросы по данным
          </p>
        </div>

        {/* Upload */}
        <FileUpload onUpload={handleUpload} loading={uploadLoading} />

        {/* Error */}
        {error && (
          <div className="fade-in" style={{
            marginTop: 16, padding: "12px 18px",
            background: "rgba(233,69,96,0.08)",
            border: "1px solid rgba(233,69,96,0.25)",
            borderRadius: 10, color: "#e94560", fontSize: 14,
          }}>
            ❌ {error}
          </div>
        )}

        {/* Summary */}
        {summary && (
          <div style={{ marginTop: 24 }}>
            <Summary summary={summary} fileName={fileName} totalRows={totalRows} />
          </div>
        )}

        {/* Preview table */}
        {preview && preview.length > 0 && (
          <div className="fade-in" style={{
            marginTop: 16,
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 16, padding: 20, overflowX: "auto",
          }}>
            <p style={{ color: "#444", fontSize: 12, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>
              Превью · первые {preview.length} строк
            </p>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr>
                  {Object.keys(preview[0]).map((col) => (
                    <th key={col} style={{
                      padding: "7px 14px", textAlign: "left",
                      color: "#e94560", borderBottom: "1px solid rgba(255,255,255,0.06)",
                      whiteSpace: "nowrap", fontWeight: 500,
                    }}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)" }}>
                    {Object.values(row).map((val, j) => (
                      <td key={j} style={{ padding: "6px 14px", color: "#999" }}>
                        {val === null || val === undefined ? "—" : String(val)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Chat */}
        {tableData && (
          <div className="fade-in" style={{
            marginTop: 20,
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 16, padding: "20px 24px",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
              <div style={{
                width: 6, height: 6, borderRadius: "50%",
                background: "#22c55e", boxShadow: "0 0 8px #22c55e",
              }} />
              <span style={{ color: "#555", fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1.5 }}>
                Чат с данными
              </span>
            </div>
            <Chat tableData={tableData} history={history} onNewMessage={setHistory} />
          </div>
        )}

      </div>
    </div>
  );
}
