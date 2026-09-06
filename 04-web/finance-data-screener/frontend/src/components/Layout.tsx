import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { to: "/datasets", label: "Датасеты" },
  { to: "/collect",  label: "Сбор" },
  { to: "/showcase", label: "Витрина" },
  { to: "/query",    label: "Запрос" },
  { to: "/sources",  label: "Источники" },
  { to: "/audit",    label: "Журнал" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-t-bg">
      <header className="bg-[#020d09] border-b border-t-border sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center gap-6 h-12">
            <div className="flex items-center gap-2 shrink-0">
              <div className="w-6 h-6 bg-t-accent rounded flex items-center justify-center">
                <span className="font-mono text-t-bg text-xs font-bold leading-none">&gt;_</span>
              </div>
              <span className="font-mono text-t-accent font-semibold tracking-wider text-sm">
                ИИ_СКРИНЕР
              </span>
            </div>
            <nav className="flex gap-0.5 flex-1 overflow-x-auto">
              {NAV.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `px-3 py-1 rounded text-xs font-mono font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? "bg-t-accent text-t-bg"
                        : "text-t-muted hover:text-t-text"
                    }`
                  }
                >
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
