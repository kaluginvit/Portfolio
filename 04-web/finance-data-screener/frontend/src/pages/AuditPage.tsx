import { useState, useEffect } from "react";
import { getAudit } from "../api/datasets";
import type { AuditRun } from "../types";

function MethodBadge({ method }: { method: string }) {
  const style =
    method === "GET"      ? "bg-blue-950/60 text-blue-300 border-blue-800/40"
    : method === "POST"   ? "bg-purple-950/60 text-purple-300 border-purple-800/40"
    : method === "DELETE" ? "bg-red-950/60 text-red-300 border-red-800/40"
    : "bg-t-card text-t-muted border-t-border";
  return (
    <span className={`px-2 py-0.5 rounded border font-mono text-xs font-semibold ${style}`}>
      {method}
    </span>
  );
}

function StatusBadge({ code }: { code: number }) {
  const style =
    code < 300 ? "bg-t-card text-t-accent border-t-border"
    : code < 400 ? "bg-amber-950/60 text-amber-300 border-amber-800/40"
    : "bg-red-950/60 text-red-300 border-red-800/40";
  return (
    <span className={`px-2 py-0.5 rounded border font-mono text-xs font-semibold ${style}`}>
      {code}
    </span>
  );
}

function formatDuration(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit", month: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

function RecordCard({ run, onClose }: { run: AuditRun; onClose: () => void }) {
  return (
    <div className="mt-2 border border-t-border bg-t-bg rounded p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-mono text-t-muted text-xs uppercase tracking-wider">Карточка запроса</span>
        <button onClick={onClose} className="font-mono text-t-muted hover:text-t-text text-lg leading-none">×</button>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs font-mono">
        <div>
          <p className="text-t-muted uppercase tracking-wider mb-1">Эндпоинт</p>
          <p className="text-t-text">{run.method} {run.endpoint}</p>
        </div>
        <div>
          <p className="text-t-muted uppercase tracking-wider mb-1">Статус / Время</p>
          <p className="text-t-text">{run.status_code} · {formatDuration(run.duration_ms)}</p>
        </div>
      </div>

      {run.request_body && (
        <div>
          <p className="font-mono text-t-muted text-xs uppercase tracking-wider mb-1">Вход (input)</p>
          <pre className="bg-t-card border border-t-border rounded p-3 text-t-text text-xs overflow-x-auto whitespace-pre-wrap break-all max-h-40">
            {JSON.stringify(run.request_body, null, 2)}
          </pre>
        </div>
      )}

      {run.response_summary && (
        <div>
          <p className="font-mono text-t-muted text-xs uppercase tracking-wider mb-1">Выход (output)</p>
          <pre className="bg-t-card border border-t-border rounded p-3 text-t-text text-xs overflow-x-auto whitespace-pre-wrap break-all max-h-40">
            {(() => {
              try { return JSON.stringify(JSON.parse(run.response_summary!), null, 2); }
              catch { return run.response_summary; }
            })()}
          </pre>
        </div>
      )}

      {run.error && (
        <div>
          <p className="font-mono text-t-muted text-xs uppercase tracking-wider mb-1">Ошибка</p>
          <p className="font-mono text-red-400 text-xs">{run.error}</p>
        </div>
      )}

      <p className="font-mono text-t-muted text-xs border-t border-t-border pt-2">
        {formatTime(run.created_at)}
      </p>
    </div>
  );
}

export default function AuditPage() {
  const [runs, setRuns]           = useState<AuditRun[]>([]);
  const [loading, setLoading]     = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    getAudit()
      .then((data) => setRuns(Array.isArray(data) ? data : []))
      .catch(() => setRuns([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="text-center py-16">
        <p className="font-mono text-t-muted text-sm animate-pulse">Загрузка журнала...</p>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="font-mono text-t-text text-sm font-semibold">Журнал пуст</p>
        <p className="font-mono text-t-muted text-xs mt-1">Операции появятся после первого запроса</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-mono text-t-text text-lg font-semibold">// Журнал операций</h1>
        <span className="font-mono text-t-muted text-xs">{runs.length} записей</span>
      </div>

      {runs.map((run) => {
        const leftBorder =
          run.status_code < 300 ? "border-l-t-accent"
          : run.status_code < 400 ? "border-l-amber-600"
          : "border-l-red-600";
        const isExpanded = expandedId === run.id;

        return (
          <div key={run.id}>
            <div
              className={`bg-t-card border border-t-border border-l-2 ${leftBorder} rounded px-4 py-3 flex items-center gap-3 flex-wrap cursor-pointer hover:border-t-accent transition-colors`}
              onClick={() => setExpandedId(isExpanded ? null : run.id)}
            >
              <MethodBadge method={run.method} />
              <StatusBadge code={run.status_code} />
              <span className="font-mono text-t-text text-sm flex-1 min-w-0 truncate">
                {run.endpoint}
              </span>
              {run.error && (
                <span className="font-mono text-red-400 text-xs truncate max-w-[200px]" title={run.error}>
                  {run.error}
                </span>
              )}
              <span className="font-mono text-t-muted text-xs whitespace-nowrap">
                {formatDuration(run.duration_ms)}
              </span>
              <span className="font-mono text-t-muted text-xs whitespace-nowrap">
                {formatTime(run.created_at)}
              </span>
              <span className="font-mono text-t-muted text-xs ml-1">
                {isExpanded ? "▲" : "▼"}
              </span>
            </div>

            {isExpanded && (
              <RecordCard run={run} onClose={() => setExpandedId(null)} />
            )}
          </div>
        );
      })}
    </div>
  );
}
