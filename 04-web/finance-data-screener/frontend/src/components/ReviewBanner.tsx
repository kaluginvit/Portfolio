interface ReviewBannerProps {
  planSteps: string[];
}

const TIPS = [
  "Добавьте конкретный период: «за сегодня», «за последние 7 дней»",
  "Укажите точный тикер или код валюты: «SBER», «USD», «GAZP»",
  "Сформулируйте числовой критерий: «объём > 1 млрд», «цена > 500»",
];

export default function ReviewBanner({ planSteps }: ReviewBannerProps) {
  const reason = planSteps.find((s) =>
    s.toLowerCase().includes("review") ||
    s.toLowerCase().includes("невозможно") ||
    s.toLowerCase().includes("неясно") ||
    s.toLowerCase().includes("уточн") ||
    s.toLowerCase().includes("отсутств")
  ) ?? planSteps[planSteps.length - 1] ?? "Запрос требует уточнения.";

  return (
    <div className="border border-amber-700/50 bg-amber-950/30 rounded p-4 space-y-3">
      <div className="flex gap-3">
        <span className="font-mono text-amber-400 text-sm leading-none mt-0.5 shrink-0">⚠</span>
        <div>
          <p className="font-mono text-sm font-semibold text-amber-300">Требуется проверка</p>
          <p className="font-mono text-xs text-amber-400/90 mt-0.5">{reason}</p>
          <p className="font-mono text-xs text-amber-500/70 mt-1">
            Автоматический сбор не запущен — уточните запрос.
          </p>
        </div>
      </div>

      <div className="border-t border-amber-800/40 pt-3">
        <p className="font-mono text-amber-500/80 text-xs uppercase tracking-wider mb-2">Что сделать:</p>
        <ul className="space-y-1">
          {TIPS.map((tip, i) => (
            <li key={i} className="flex gap-2 font-mono text-xs text-amber-400/70">
              <span className="text-amber-600 shrink-0">{i + 1}.</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
