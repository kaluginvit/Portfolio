import type { CollectionPlan } from "../types";
import Badge from "./Badge";

interface PlanPreviewProps {
  plan: CollectionPlan;
}

const CONFIDENCE_STYLES: Record<string, string> = {
  high:   "text-t-accent",
  medium: "text-amber-400",
  low:    "text-red-400",
};

const CONFIDENCE_LABELS: Record<string, string> = {
  high:   "Высокая",
  medium: "Средняя",
  low:    "Низкая",
};

export default function PlanPreview({ plan }: PlanPreviewProps) {
  const filtersEntries = Object.entries(plan.filters ?? {});

  return (
    <div className="bg-t-bg border border-t-border rounded p-4 space-y-3 font-mono">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-t-muted text-xs uppercase tracking-wider">Источник:</span>
        <Badge source={plan.source} />
        <span className={`ml-auto text-xs font-medium ${CONFIDENCE_STYLES[plan.confidence] ?? "text-t-muted"}`}>
          Уверенность: {CONFIDENCE_LABELS[plan.confidence] ?? plan.confidence}
        </span>
      </div>

      <div>
        <p className="text-t-muted text-xs uppercase tracking-wider mb-1">URL запроса</p>
        <a
          href={plan.api_url}
          target="_blank"
          rel="noreferrer"
          className="text-t-accent text-xs hover:underline break-all"
        >
          {plan.api_url}
        </a>
      </div>

      {plan.fields_to_keep.length > 0 && (
        <div>
          <p className="text-t-muted text-xs uppercase tracking-wider mb-1">Поля</p>
          <div className="flex flex-wrap gap-1">
            {plan.fields_to_keep.map((f) => (
              <span
                key={f}
                className="text-xs bg-t-card border border-t-border text-t-text px-2 py-0.5 rounded"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      )}

      {filtersEntries.length > 0 && (
        <div>
          <p className="text-t-muted text-xs uppercase tracking-wider mb-1">Фильтры</p>
          <pre className="text-xs bg-t-bg border border-t-border text-t-text rounded p-2 break-all whitespace-pre-wrap">
            {JSON.stringify(plan.filters, null, 2)}
          </pre>
        </div>
      )}

      {plan.plan_steps.length > 0 && (
        <div>
          <p className="text-t-muted text-xs uppercase tracking-wider mb-1">Шаги плана</p>
          <ol className="list-none space-y-0.5">
            {plan.plan_steps.map((step, i) => (
              <li key={i} className="text-xs text-t-text flex gap-2">
                <span className="text-t-accent shrink-0">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
