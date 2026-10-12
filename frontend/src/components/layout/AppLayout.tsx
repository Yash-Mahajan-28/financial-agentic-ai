import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import clsx from "clsx";
import {
  LayoutDashboard,
  UploadCloud,
  Receipt,
  PieChart,
  AlertTriangle,
  TrendingUp,
  Bot,
  Settings,
  Sun,
  Moon,
  ShieldCheck
} from "lucide-react";
import { useTheme } from "../../hooks/useTheme";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload & Review", icon: UploadCloud },
  { to: "/transactions", label: "Transactions", icon: Receipt },
  { to: "/budgets", label: "Budgets & 50/30/20", icon: PieChart },
  { to: "/insights", label: "Insights & Alerts", icon: AlertTriangle },
  { to: "/forecast", label: "Cash Forecast", icon: TrendingUp },
  { to: "/advisor", label: "AI Advisor", icon: Bot },
  { to: "/system", label: "System & Health", icon: Settings },
];

export function AppLayout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-screen w-full bg-canvas overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-line bg-surface flex flex-col justify-between shrink-0">
        <div>
          {/* Logo & Brand */}
          <div className="h-16 px-6 flex items-center gap-3 border-b border-line">
            <div className="h-9 w-9 rounded-xl bg-accent flex items-center justify-center text-white shadow-sm font-bold text-lg">
              ₹
            </div>
            <div>
              <span className="font-bold text-base text-ink tracking-tight flex items-center gap-1.5">
                FinAgentic <span className="text-xs px-1.5 py-0.5 rounded bg-accent/15 text-accent font-semibold">AI</span>
              </span>
              <p className="text-[11px] text-muted font-medium">Personal Finance Agent</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    clsx(
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-accent/15 text-accent font-semibold"
                        : "text-muted hover:bg-sunken hover:text-ink"
                    )
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Footer controls: System status & Theme toggle */}
        <div className="p-4 border-t border-line space-y-3">
          <div className="flex items-center justify-between text-xs text-muted px-2 py-1.5 rounded-lg bg-sunken">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-pass animate-pulse"></span>
              <span className="font-medium text-ink">Engine Live</span>
            </span>
            <span className="text-[11px] text-muted">v1.0.0</span>
          </div>

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-accent/20 flex items-center justify-center text-accent text-xs font-semibold">
                AS
              </div>
              <div className="leading-tight">
                <p className="text-xs font-semibold text-ink">Aarav Sharma</p>
                <p className="text-[10px] text-muted">demo@agentic.finance</p>
              </div>
            </div>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-muted hover:bg-sunken hover:text-ink transition-colors"
              title="Toggle theme"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
