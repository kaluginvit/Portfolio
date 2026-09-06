import { useState, useEffect } from "react";
import type { Dataset, QueryResponse } from "../types";
import { getDatasets, queryDataset } from "../api/datasets";

interface HistoryItem {
  question: string;
  response: QueryResponse;
}

export default function QueryPage() {
  const [datasets, setDatasets]     = useState<Dataset[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [question, setQuestion]     = useState("");
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState<QueryResponse | null>(null);
  const [error, setError]           = useState<string | null>(null);
  const [history, setHistory]       = useState<HistoryItem[]>([]);

  useEffect(() => {
    getDatasets().then((data) => {
      const withRecords = data.filter((d) => d.records_count > 0);
      setDatasets(withRecords);
      if (withRecords.length > 0) setSelectedId(withRecords[0].id);
    });
  }, []);

  async function handleAsk() {
    if (!question.trim() || !selectedId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await queryDataset(selectedId, question.trim());
      setResult(res);
      setHistory((prev) => [{ question: question.trim(), response: res }, ...prev].slice(0, 5));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка запроса к LLM");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  }

  const selectedDataset = datasets.find((d) => d.id === selectedId);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="font-mono text-t-text text-lg font-semibold">// Запрос к данным</h1>
        <p className="font-mono text-t-muted text-sm mt-0.5">
          Задайте вопрос на русском языке — ИИ ответит на основе собранных записей
        </p>
      </div>

      {datasets.length === 0 ? (
        <div className="border border-t-border bg-t-card rounded p-4">
          <p className="font-mono text-t-muted text-sm">
            Нет датасетов с данными. Сначала соберите данные в разделе «Сбор».
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <label className="block font-mono text-t-muted text-xs uppercase tracking-wider mb-1.5">
              Датасет
            </label>
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              disabled={loading}
              className="w-full bg-t-bg border border-t-border text-t-text font-mono text-sm rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-t-accent focus:border-t-accent disabled:opacity-50"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} · {d.records_count} записей · {(d.source ?? "—").toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-mono text-t-muted text-xs uppercase tracking-wider mb-1.5">
              Вопрос
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={3}
              placeholder="Например: какие акции выросли больше всего? какой курс доллара?"
              className="w-full bg-t-bg border border-t-border text-t-text font-mono text-sm rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-t-accent focus:border-t-accent resize-none disabled:opacity-50 placeholder:text-t-muted/50"
            />
            <p className="font-mono text-t-muted/60 text-xs mt-1">Enter — отправить · Shift+Enter — новая строка</p>
          </div>

          <button
            onClick={handleAsk}
            disabled={loading || !question.trim() || !selectedId}
            className="px-4 py-2 bg-t-accent text-t-bg font-mono text-sm font-semibold rounded hover:bg-t-dim disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Анализирую..." : "Спросить →"}
          </button>
        </div>
      )}

      {/* Результат */}
      {loading && (
        <div className="text-center py-8">
          <p className="font-mono text-t-muted text-sm animate-pulse">
            Анализирую {selectedDataset?.records_count ?? 0} записей...
          </p>
        </div>
      )}

      {error && (
        <div className="border border-red-900/50 bg-red-950/20 rounded p-4">
          <p className="font-mono text-red-400 text-sm font-semibold">✗ Ошибка</p>
          <p className="font-mono text-red-400/80 text-xs mt-1">{error}</p>
        </div>
      )}

      {result && !loading && (
        <div className="border border-t-border bg-t-card rounded p-4 space-y-3">
          {result.needs_review ? (
            <div className="border border-amber-700/50 bg-amber-950/30 rounded p-3 flex gap-2">
              <span className="font-mono text-amber-400 text-sm shrink-0">⚠</span>
              <div>
                <p className="font-mono text-amber-300 text-sm font-semibold">Данных недостаточно</p>
                <p className="font-mono text-amber-400/90 text-xs mt-0.5">{result.review_reason}</p>
              </div>
            </div>
          ) : (
            <p className="font-mono text-t-text text-sm leading-relaxed">{result.answer}</p>
          )}
          <p className="font-mono text-t-muted text-xs border-t border-t-border pt-2">
            Проанализировано записей: <span className="text-t-accent">{result.records_used}</span>
          </p>
        </div>
      )}

      {/* История */}
      {history.length > 1 && (
        <div className="space-y-2">
          <p className="font-mono text-t-muted text-xs uppercase tracking-wider">История</p>
          {history.slice(1).map((item, i) => (
            <div key={i} className="border border-t-border/50 rounded p-3 space-y-1">
              <p className="font-mono text-t-muted text-xs">
                <span className="text-t-accent">?</span> {item.question}
              </p>
              {item.response.needs_review ? (
                <p className="font-mono text-amber-400/70 text-xs">⚠ {item.response.review_reason}</p>
              ) : (
                <p className="font-mono text-t-text/70 text-xs line-clamp-2">{item.response.answer}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
