interface BadgeProps {
  source: string | null;
  className?: string;
}

const SOURCE_STYLES: Record<string, string> = {
  moex: "bg-blue-950/60 text-blue-300 border border-blue-800/40",
  cbr:  "bg-emerald-950/60 text-t-accent border border-t-border",
  rbc:  "bg-orange-950/60 text-orange-300 border border-orange-800/40",
  tass: "bg-orange-950/60 text-orange-300 border border-orange-800/40",
};

const SOURCE_LABELS: Record<string, string> = {
  moex: "MOEX",
  cbr:  "ЦБ РФ",
  rbc:  "РБК",
  tass: "ТАСС",
};

export default function Badge({ source, className = "" }: BadgeProps) {
  const key = source?.toLowerCase() ?? "";
  const style = SOURCE_STYLES[key] ?? "bg-t-card text-t-muted border border-t-border";
  const label = SOURCE_LABELS[key] ?? (source ?? "—");

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium ${style} ${className}`}>
      {label}
    </span>
  );
}
