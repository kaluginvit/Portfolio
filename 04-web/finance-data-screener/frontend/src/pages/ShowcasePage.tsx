import { useState, useEffect, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  useReactTable, getCoreRowModel, flexRender, type ColumnDef,
} from "@tanstack/react-table";
import { getDatasets, getRecords } from "../api/datasets";
import Badge from "../components/Badge";
import type { Dataset, DataRecord } from "../types";

const NUMERIC_KEYS = ["LAST", "VALTODAY", "VOLTODAY", "Value", "price", "value", "amount", "Nominal"];
const LABEL_KEYS   = ["SECID", "CharCode", "SHORTNAME", "name", "title", "Name"];

function findNumericKey(data: Record<string, unknown>): string | null {
  for (const key of NUMERIC_KEYS) {
    const v = data[key];
    if (v !== null && v !== undefined && v !== "" && !isNaN(Number(v))) return key;
  }
  for (const [key, val] of Object.entries(data)) {
    if (val !== null && val !== undefined && val !== "" && !isNaN(Number(val))) return key;
  }
  return null;
}

function findLabelKey(data: Record<string, unknown>): string | null {
  for (const key of LABEL_KEYS) {
    if (key in data && data[key] !== null && data[key] !== undefined) return key;
  }
  return null;
}

function formatAxisValue(v: number): string {
  if (Math.abs(v) >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(0)}M`;
  if (Math.abs(v) >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return String(v);
}

const LIMIT_OPTIONS = [50, 100, 500];

export default function ShowcasePage() {
  const [datasets, setDatasets]     = useState<Dataset[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [records, setRecords]       = useState<DataRecord[]>([]);
  const [loading, setLoading]       = useState(false);
  const [limit, setLimit]           = useState(100);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => { getDatasets().then(setDatasets).catch(() => {}); }, []);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setExpandedId(null);
    if (!id) { setRecords([]); return; }
    setLoading(true);
    getRecords(id)
      .then((data) => setRecords(Array.isArray(data) ? data : []))
      .catch(() => setRecords([]))
      .finally(() => setLoading(false));
  };

  const selectedDataset = datasets.find((d) => d.id === selectedId);

  const visibleRecords = useMemo(() => records.slice(0, limit), [records, limit]);

  const tableData = useMemo<Record<string, unknown>[]>(
    () => visibleRecords.map((r) => r.data),
    [visibleRecords]
  );

  const columns = useMemo<ColumnDef<Record<string, unknown>>[]>(() => {
    if (tableData.length === 0) return [];
    const keys = Object.keys(tableData[0]).slice(0, 8);
    return keys.map((key) => ({
      id: key,
      header: key,
      accessorFn: (row: Record<string, unknown>) => row[key],
      cell: (info) => {
        const val = info.getValue();
        if (val === null || val === undefined) return "—";
        return String(val).slice(0, 60);
      },
    }));
  }, [tableData]);

  const table = useReactTable({ data: tableData, columns, getCoreRowModel: getCoreRowModel() });

  const numericKey = useMemo(
    () => (records.length > 0 ? findNumericKey(records[0].data) : null),
    [records]
  );
  const labelKey = useMemo(
    () => (records.length > 0 ? findLabelKey(records[0].data) : null),
    [records]
  );

  const chartData = useMemo(() => {
    if (!numericKey) return [];
    return visibleRecords.slice(0, 15).map((r, i) => ({
      name: labelKey ? String(r.data[labelKey] ?? `#${i + 1}`).slice(0, 12) : `#${i + 1}`,
      value: Number(r.data[numericKey]) || 0,
    }));
  }, [visibleRecords, numericKey, labelKey]);

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(records, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${selectedDataset?.name ?? "records"}.json`; a.click();
    URL.revokeObjectURL(url);
  };

  const exportCSV = () => {
    if (tableData.length === 0) return;
    const keys = Object.keys(tableData[0]);
    const header = keys.join(",");
    const rows = tableData.map((r) =>
      keys.map((k) => {
        const v = r[k];
        if (v === null || v === undefined) return "";
        const s = String(v);
        return s.includes(",") || s.includes('"') || s.includes("\n") ? `"${s.replace(/"/g, '""')}"` : s;
      }).join(",")
    );
    const blob = new Blob(["﻿" + [header, ...rows].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${selectedDataset?.name ?? "records"}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header + selector */}
      <div className="flex items-center gap-4 flex-wrap">
        <h1 className="font-mono text-t-text text-lg font-semibold">// Витрина данных</h1>
        <select
          value={selectedId}
          onChange={(e) => handleSelect(e.target.value)}
          className="bg-t-bg border border-t-border text-t-text font-mono text-sm rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-t-accent focus:border-t-accent"
        >
          <option value="">— выберите датасет —</option>
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.records_count} записей)
            </option>
          ))}
        </select>
        {selectedDataset?.source && <Badge source={selectedDataset.source} />}
      </div>

      {!selectedId && (
        <div className="text-center py-16">
          <p className="font-mono text-t-muted text-sm">Выберите датасет для просмотра данных</p>
        </div>
      )}

      {selectedId && loading && (
        <div className="text-center py-16">
          <p className="font-mono text-t-muted text-sm animate-pulse">Загрузка записей...</p>
        </div>
      )}

      {selectedId && !loading && records.length === 0 && (
        <div className="text-center py-16">
          <p className="font-mono text-t-text text-sm font-semibold">Данных пока нет</p>
          <p className="font-mono text-t-muted text-xs mt-1">
            Перейдите в «Сбор» и запустите сбор для этого датасета
          </p>
        </div>
      )}

      {selectedId && !loading && records.length > 0 && (
        <>
          {/* Stats + limit */}
          <div className="flex items-center gap-4 flex-wrap font-mono text-sm">
            <span className="text-t-muted">
              Записей: <span className="text-t-text font-semibold">{records.length}</span>
            </span>
            {selectedDataset?.source && (
              <span className="text-t-muted">
                Источник: <span className="text-t-accent uppercase">{selectedDataset.source}</span>
              </span>
            )}
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-t-muted text-xs">Показать:</span>
              <div className="flex gap-1">
                {LIMIT_OPTIONS.map((l) => (
                  <button
                    key={l}
                    onClick={() => setLimit(l)}
                    className={`px-2 py-0.5 rounded border text-xs font-mono transition-colors ${
                      limit === l
                        ? "bg-t-accent text-t-bg border-t-accent"
                        : "border-t-border text-t-muted hover:border-t-accent hover:text-t-accent"
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Chart */}
          {numericKey && chartData.length > 0 && (
            <div className="bg-t-card border border-t-border rounded-lg p-4">
              <p className="font-mono text-t-muted text-xs mb-4">
                График: <span className="text-t-accent">{numericKey}</span>
                <span className="text-t-muted"> (первые {chartData.length} записей)</span>
              </p>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData} margin={{ top: 0, right: 16, left: 0, bottom: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#0e2921" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11, fill: "#4a9985", fontFamily: "monospace" }}
                    angle={-40}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#4a9985", fontFamily: "monospace" }}
                    width={70}
                    tickFormatter={formatAxisValue}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#050f0c",
                      border: "1px solid #0e2921",
                      borderRadius: "6px",
                      fontFamily: "monospace",
                      fontSize: "12px",
                      color: "#c8f5ec",
                    }}
                    formatter={(value) => [
                      typeof value === "number" ? value.toLocaleString("ru-RU") : value,
                      numericKey,
                    ]}
                  />
                  <Bar dataKey="value" fill="#00d4aa" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Export */}
          <div className="flex gap-2">
            <button
              onClick={exportJSON}
              className="border border-t-border text-t-muted font-mono text-xs rounded px-3 py-1.5 hover:border-t-accent hover:text-t-accent transition-colors"
            >
              Экспорт JSON
            </button>
            <button
              onClick={exportCSV}
              className="border border-t-border text-t-muted font-mono text-xs rounded px-3 py-1.5 hover:border-t-accent hover:text-t-accent transition-colors"
            >
              Экспорт CSV
            </button>
          </div>

          {/* Table */}
          <div className="bg-t-card border border-t-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto max-h-[520px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-t-border bg-t-bg sticky top-0 z-10">
                  {table.getHeaderGroups().map((hg) => (
                    <tr key={hg.id}>
                      {hg.headers.map((h) => (
                        <th key={h.id} className="px-3 py-2.5 text-left font-mono text-t-muted text-xs uppercase tracking-wider whitespace-nowrap">
                          {flexRender(h.column.columnDef.header, h.getContext())}
                        </th>
                      ))}
                    </tr>
                  ))}
                </thead>
                <tbody className="divide-y divide-t-border/50">
                  {table.getRowModel().rows.map((row, idx) => {
                    const record = visibleRecords[idx];
                    const isOpen = expandedId === record?.id;
                    return (
                      <>
                        <tr
                          key={row.id}
                          className="hover:bg-t-accent/5 transition-colors cursor-pointer"
                          onClick={() => setExpandedId(isOpen ? null : record?.id ?? null)}
                        >
                          {row.getVisibleCells().map((cell) => (
                            <td key={cell.id} className="px-3 py-2 font-mono text-t-text text-xs whitespace-nowrap max-w-[200px] truncate">
                              {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                          ))}
                          <td className="px-3 py-2 font-mono text-t-muted text-xs whitespace-nowrap">
                            {isOpen ? "▲" : "▼"}
                          </td>
                        </tr>
                        {isOpen && record && (
                          <tr key={`${row.id}-expand`}>
                            <td colSpan={columns.length + 1} className="px-3 py-3 bg-t-bg border-t border-t-border">
                              <div>
                                <p className="font-mono text-t-muted text-xs uppercase tracking-wider mb-2">
                                  Полная запись (record_json) · {record.source?.toUpperCase()} · {new Date(record.collected_at).toLocaleString("ru-RU")}
                                </p>
                                <pre className="font-mono text-t-text text-xs bg-t-card border border-t-border rounded p-3 overflow-x-auto whitespace-pre-wrap break-all max-h-64">
                                  {JSON.stringify(record.data, null, 2)}
                                </pre>
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 font-mono text-t-muted text-xs border-t border-t-border">
              Показано {visibleRecords.length} из {records.length} записей · до 8 столбцов · кликни строку для полного JSON
            </div>
          </div>
        </>
      )}
    </div>
  );
}
