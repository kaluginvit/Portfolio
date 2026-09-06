import { useState, useRef } from "react";

export default function FileUpload({ onUpload, loading }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    onUpload(formData, file.name);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div
      onClick={() => !loading && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      style={{
        position: "relative",
        borderRadius: 16,
        padding: "52px 32px",
        textAlign: "center",
        cursor: loading ? "not-allowed" : "pointer",
        background: dragging
          ? "rgba(233,69,96,0.06)"
          : "rgba(255,255,255,0.02)",
        border: `1.5px dashed ${dragging ? "#e94560" : "rgba(255,255,255,0.1)"}`,
        backdropFilter: "blur(12px)",
        transition: "all 0.25s ease",
        boxShadow: dragging ? "0 0 40px rgba(233,69,96,0.15)" : "none",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {loading ? (
        <div>
          <div style={{ fontSize: 36, marginBottom: 12, animation: "pulse 1.2s infinite" }}>⚡</div>
          <p style={{ color: "#e94560", fontWeight: 500 }}>Анализируем данные...</p>
          <p style={{ color: "#555", fontSize: 13, marginTop: 4 }}>Claude читает таблицу</p>
        </div>
      ) : (
        <div>
          <div style={{
            width: 64, height: 64, margin: "0 auto 16px",
            background: "linear-gradient(135deg, rgba(233,69,96,0.2), rgba(99,69,233,0.2))",
            borderRadius: 16, display: "flex", alignItems: "center",
            justifyContent: "center", fontSize: 28,
          }}>
            📊
          </div>
          <p style={{ color: "#ccc", fontWeight: 500, marginBottom: 6 }}>
            {dragging ? "Отпустите файл" : "Перетащите CSV или Excel"}
          </p>
          <p style={{ color: "#444", fontSize: 13 }}>
            или <span style={{ color: "#e94560" }}>нажмите для выбора</span> · .csv, .xlsx, .xls
          </p>
        </div>
      )}
    </div>
  );
}
