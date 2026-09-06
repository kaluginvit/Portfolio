import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { Dataset, PlanResponse, CollectResponse } from "../types";
import { getDatasets, planAndCollect, collectDataset } from "../api/datasets";
import PlanPreview from "../components/PlanPreview";
import ReviewBanner from "../components/ReviewBanner";

type Phase =
  | { kind: "idle" }
  | { kind: "planning" }
  | { kind: "planned"; result: PlanResponse; datasetId: string }
  | { kind: "collecting" }
  | { kind: "done"; result: CollectResponse }
  | { kind: "error"; message: string };

export default function CollectPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [query, setQuery] = useState("");
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });

  useEffect(() => {
    getDatasets().then((data) => {
      setDatasets(data);
      if (data.length > 0) setSelectedDatasetId(data[0].id);
    });
  }, []);

  async function handlePlan() {
    if (!query.trim() || !selectedDatasetId) return;
    setPhase({ kind: "planning" });
    try {
      const result = await planAndCollect(query.trim(), selectedDatasetId);
      setPhase({ kind: "planned", result, datasetId: selectedDatasetId });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Ошибка планирования";
      setPhase({ kind: "error", message: msg });
    }
  }

  async function handleCollect() {
    if (phase.kind !== "planned") return;
    const { result, datasetId } = phase;
    setPhase({ kind: "collecting" });
    try {
      const collected = await collectDataset(datasetId, result.agent_run_id);
      setPhase({ kind: "done", result: collected });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Ошибка сбора данных";
      setPhase({ kind: "error", message: msg });
    }
  }

  function handleReset() {
    setPhase({ kind: "idle" });
    setQuery("");
  }

  const navigate = useNavigate();
  const isLoading = phase.kind === "planning" || phase.kind === "collecting";

  const stepIndex =
    phase.kind === "idle" || phase.kind === "planning" ? 0
    : phase.kind === "planned" ? 1
    : phase.kind === "collecting" ? 2
    : phase.kind === "done" ? 3 : 0;

  const steps = ["Запрос", "План", "Сбор", "Готово"];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="font-mono text-t-text text-lg font-semibold">// Сбор данных</h1>
        <p className="font-mono text-t-muted text-sm mt-0.5">
          Опишите запрос — ИИ построит план и соберёт данные
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-0">
        {steps.map((label, i) => (
          <div key={i} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center gap-1">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-semibold transition-colors ${
                i < stepIndex
                  ? "bg-t-accent text-t-bg"
                  : i === stepIndex
                  ? "bg-t-accent text-t-bg ring-2 ring-t-accent/30"
                  : "bg-t-card text-t-muted border border-t-border"
              }`}>
                {i < stepIndex ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                ) : i + 1}
              </div>
              <span className={`font-mono text-xs whitespace-nowrap ${
                i <= stepIndex ? "text-t-accent" : "text-t-muted"
              }`}>
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`h-px flex-1 mx-2 mb-5 transition-colors ${
                i < stepIndex ? "bg-t-accent" : "bg-t-border"
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Форма */}
      <div className="space-y-3">
        {datasets.length === 0 ? (
          <p className="font-mono text-t-muted text-sm">
            Сначала создайте набор данных в разделе «Датасеты».
          </p>
        ) : (
          <div>
            <label className="block font-mono text-t-muted text-xs uppercase tracking-wider mb-1.5">
              Набор данных
            </label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              disabled={isLoading}
              className="w-full bg-t-bg border border-t-border text-t-text font-mono text-sm rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-t-accent focus:border-t-accent disabled:opacity-50"
            >
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block font-mono text-t-muted text-xs uppercase tracking-wider mb-1.5">
            Запрос
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading || phase.kind === "done"}
            rows={3}
            placeholder="Например: акции с объёмом торгов > 1 млрд за сегодня"
            className="w-full bg-t-bg border border-t-border text-t-text font-mono text-sm rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-t-accent focus:border-t-accent resize-none disabled:opacity-50 placeholder:text-t-muted/50"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={handlePlan}
            disabled={isLoading || !query.trim() || !selectedDatasetId || phase.kind === "done"}
            className="px-4 py-2 bg-t-accent text-t-bg font-mono text-sm font-semibold rounded hover:bg-t-dim disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {phase.kind === "planning" ? "Планирование..." : "Построить план"}
          </button>

          {phase.kind !== "idle" && (
            <button
              onClick={handleReset}
              disabled={isLoading}
              className="px-4 py-2 border border-t-border text-t-muted font-mono text-sm rounded hover:border-t-accent hover:text-t-accent disabled:opacity-50 transition-colors"
            >
              Сбросить
            </button>
          )}
        </div>
      </div>

      {/* Результат планирования */}
      {phase.kind === "planned" && (
        <div className="space-y-4">
          <div>
            <h2 className="font-mono text-t-muted text-xs uppercase tracking-wider mb-2">
              Plan Preview
            </h2>
            <PlanPreview plan={phase.result.plan} />
          </div>

          {phase.result.plan.needs_review ? (
            <ReviewBanner planSteps={phase.result.plan.plan_steps} />
          ) : (
            <button
              onClick={handleCollect}
              className="w-full px-4 py-2 bg-t-accent text-t-bg font-mono text-sm font-semibold rounded hover:bg-t-dim transition-colors"
            >
              Собрать данные →
            </button>
          )}
        </div>
      )}

      {/* Сбор в процессе */}
      {phase.kind === "collecting" && (
        <div className="text-center py-8 font-mono text-t-muted text-sm animate-pulse">
          Идёт сбор данных...
        </div>
      )}

      {/* Успех */}
      {phase.kind === "done" && (
        <div className="border border-t-border bg-t-card rounded p-4">
          <p className="font-mono text-t-accent text-sm font-semibold">✓ Данные собраны</p>
          <p className="font-mono text-t-muted text-xs mt-1">
            Записей: <span className="text-t-text font-semibold">{phase.result.records_saved}</span>
            {" · "}Источник: <span className="text-t-accent">{phase.result.source.toUpperCase()}</span>
          </p>
          <div className="flex gap-3 mt-3">
            <button
              onClick={() => navigate(`/showcase?dataset=${phase.result.dataset_id}`)}
              className="px-3 py-1.5 bg-t-accent text-t-bg font-mono text-xs font-semibold rounded hover:bg-t-dim transition-colors"
            >
              Открыть витрину →
            </button>
            <button onClick={handleReset} className="font-mono text-xs text-t-muted hover:text-t-accent transition-colors">
              Новый запрос
            </button>
          </div>
        </div>
      )}

      {/* Ошибка */}
      {phase.kind === "error" && (
        <div className="border border-red-900/50 bg-red-950/20 rounded p-4">
          <p className="font-mono text-red-400 text-sm font-semibold">✗ Ошибка</p>
          <p className="font-mono text-red-400/80 text-xs mt-1">{phase.message}</p>
          <button onClick={handleReset} className="mt-3 font-mono text-xs text-red-400 hover:underline">
            Попробовать снова
          </button>
        </div>
      )}
    </div>
  );
}
