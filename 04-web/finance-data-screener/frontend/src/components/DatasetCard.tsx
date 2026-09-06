import { useNavigate } from "react-router-dom";
import type { Dataset } from "../types";
import Badge from "./Badge";

interface Props {
  dataset: Dataset;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DatasetCard({ dataset }: Props) {
  const navigate = useNavigate();

  return (
    <div className="bg-t-card border border-t-border rounded-lg p-4 hover:border-t-accent transition-all group">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0 flex-1">
          <h3 className="font-mono font-semibold text-t-text truncate group-hover:text-t-accent transition-colors">
            {dataset.name}
          </h3>
          <p className="font-mono text-xs text-t-muted mt-0.5 truncate">{dataset.query}</p>
        </div>
        <Badge source={dataset.source} />
      </div>

      <div className="flex items-center justify-between text-xs border-t border-t-border pt-3">
        <span className="font-mono text-t-muted">{formatDate(dataset.created_at)}</span>
        <span className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${dataset.records_count > 0 ? "bg-t-accent" : "bg-t-border"}`} />
          <span className="font-mono font-semibold text-t-accent">
            {dataset.records_count.toLocaleString("ru-RU")}
          </span>
          <span className="font-mono text-t-muted">записей</span>
        </span>
      </div>

      {dataset.records_count > 0 && (
        <button
          onClick={() => navigate(`/showcase?dataset=${dataset.id}`)}
          className="mt-3 w-full border border-t-border text-t-muted text-xs font-mono rounded py-1.5 hover:border-t-accent hover:text-t-accent transition-colors"
        >
          Открыть витрину →
        </button>
      )}
    </div>
  );
}
