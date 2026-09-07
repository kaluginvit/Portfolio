export default function DemoModeBanner() {
  return (
    <div className="bg-t-accent/10 border-b border-t-accent/30 px-4 py-1.5">
      <p className="max-w-6xl mx-auto font-mono text-t-accent text-xs">
        <span className="font-semibold">Demo Mode</span>
        {" — "}preloaded public/sample data (MOEX, CBR). Write actions disabled.
      </p>
    </div>
  );
}
