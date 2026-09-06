import { useState, useEffect } from "react";
import type { Dataset } from "../types";
import { getDatasets, createDataset } from "../api/datasets";
import DatasetCard from "../components/DatasetCard";
import CreateDatasetModal from "../components/CreateDatasetModal";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await getDatasets();
      setDatasets(data);
    } catch {
      setError("Не удалось загрузить наборы данных");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(form: { name: string; query: string }) {
    const created = await createDataset(form);
    setDatasets((prev) => [created, ...prev]);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-mono text-t-text text-lg font-semibold">// Наборы данных</h1>
          <p className="font-mono text-t-muted text-sm mt-0.5">
            {datasets.length > 0
              ? `${datasets.length} набор${datasets.length === 1 ? "" : datasets.length < 5 ? "а" : "ов"}`
              : "Создайте первый набор данных"}
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-t-accent text-t-bg font-mono text-xs font-semibold rounded hover:bg-t-dim transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Создать
        </button>
      </div>

      {loading && (
        <div className="text-center py-16 font-mono text-t-muted text-sm">Загрузка...</div>
      )}

      {error && (
        <div className="text-center py-16">
          <p className="font-mono text-red-400 text-sm">{error}</p>
          <button onClick={load} className="mt-3 font-mono text-xs text-t-accent hover:underline">
            Попробовать снова
          </button>
        </div>
      )}

      {!loading && !error && datasets.length === 0 && (
        <div className="text-center py-20">
          <div className="w-12 h-12 border border-t-border rounded-xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-t-border" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.625c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
            </svg>
          </div>
          <p className="font-mono text-t-text font-semibold text-sm">Наборов данных пока нет</p>
          <p className="font-mono text-t-muted text-xs mt-1 mb-4">Создайте первый набор и соберите данные</p>
          <button
            onClick={() => setShowModal(true)}
            className="px-5 py-2 bg-t-accent text-t-bg font-mono text-xs font-semibold rounded hover:bg-t-dim transition-colors"
          >
            Создать набор данных
          </button>
        </div>
      )}

      {!loading && !error && datasets.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {datasets.map((ds) => (
            <DatasetCard key={ds.id} dataset={ds} />
          ))}
        </div>
      )}

      {showModal && (
        <CreateDatasetModal
          onClose={() => setShowModal(false)}
          onCreate={handleCreate}
        />
      )}
    </div>
  );
}
