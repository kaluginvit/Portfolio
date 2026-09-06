import { useState } from "react";
import type { DatasetCreate } from "../types";

interface Props {
  onClose: () => void;
  onCreate: (data: DatasetCreate) => Promise<void>;
}

export default function CreateDatasetModal({ onClose, onCreate }: Props) {
  const [name, setName] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onCreate({ name: name.trim(), query: query.trim() });
      onClose();
    } catch {
      setError("Не удалось создать набор данных. Попробуйте снова.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-t-card border border-t-border rounded-lg w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-t-border">
          <h2 className="font-mono text-t-text font-semibold text-sm">// Новый набор данных</h2>
          <button
            onClick={onClose}
            className="font-mono text-t-muted hover:text-t-text text-xl leading-none transition-colors"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 py-4 space-y-4">
          <div>
            <label className="block font-mono text-t-muted text-xs uppercase tracking-wider mb-1.5">
              Название
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Акции с большим объёмом"
              className="w-full bg-t-bg border border-t-border text-t-text font-mono text-sm rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-t-accent focus:border-t-accent placeholder:text-t-muted/50"
              autoFocus
            />
          </div>

          <div>
            <label className="block font-mono text-t-muted text-xs uppercase tracking-wider mb-1.5">
              Запрос
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="акции с объёмом торгов больше 1 млрд рублей за сегодня"
              rows={3}
              className="w-full bg-t-bg border border-t-border text-t-text font-mono text-sm rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-t-accent focus:border-t-accent resize-none placeholder:text-t-muted/50"
            />
            <p className="font-mono text-t-muted text-xs mt-1">
              Запрос на русском — ИИ разберёт его при запуске сбора
            </p>
          </div>

          {error && <p className="font-mono text-red-400 text-xs">{error}</p>}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-t-border text-t-muted font-mono text-sm rounded hover:border-t-accent hover:text-t-accent transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim() || !query.trim()}
              className="flex-1 px-4 py-2 bg-t-accent text-t-bg font-mono text-sm font-semibold rounded hover:bg-t-dim disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Создание..." : "Создать"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
