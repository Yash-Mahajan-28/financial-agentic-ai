import React from "react";
import clsx from "clsx";
import { X, Loader2 } from "lucide-react";

// Card
export function Card({
  children,
  className,
  title,
  subtitle,
  action
}: {
  children: React.ReactNode;
  className?: string;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className={clsx("rounded-xl border border-line bg-surface p-5 shadow-sm transition-all", className)}>
      {(title || subtitle || action) && (
        <div className="mb-4 flex items-start justify-between">
          <div>
            {title && <h3 className="text-base font-semibold text-ink">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

// Badge
export function Badge({
  variant = "default",
  children,
  className
}: {
  variant?: "default" | "pass" | "fail" | "warn" | "accent" | "muted";
  children: React.ReactNode;
  className?: string;
}) {
  const styles = {
    default: "bg-sunken text-muted border-line",
    pass: "bg-pass-soft text-pass border-pass/20",
    fail: "bg-fail-soft text-fail border-fail/20",
    warn: "bg-warn-soft text-warn border-warn/20",
    accent: "bg-accent-soft text-accent border-accent/20",
    muted: "bg-sunken text-faint border-line"
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        styles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

// Button
export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  className,
  disabled,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}) {
  const base = "inline-flex items-center justify-center font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const sizes = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-5 py-2.5 text-base gap-2.5"
  };
  const variants = {
    primary: "bg-accent text-white hover:bg-accent/90 shadow-sm",
    secondary: "bg-sunken text-ink hover:bg-sunken/80 border border-line",
    danger: "bg-fail text-white hover:bg-fail/90",
    ghost: "text-muted hover:bg-sunken hover:text-ink"
  };

  return (
    <button
      className={clsx(base, sizes[size], variants[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}

// Modal
export function Modal({
  isOpen,
  onClose,
  title,
  children
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy/60 backdrop-blur-sm">
      <div className="relative w-full max-w-lg rounded-2xl border border-line bg-surface p-6 shadow-xl animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between pb-4 border-b border-line">
          <h2 className="text-lg font-semibold text-ink">{title}</h2>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted hover:bg-sunken hover:text-ink">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}

// Loading State
export function LoadingState({ message = "Loading financial data..." }: { message?: string }) {
  return (
    <div className="flex min-h-[240px] flex-col items-center justify-center gap-3">
      <Loader2 className="h-8 w-8 animate-spin text-accent" />
      <p className="text-sm text-muted">{message}</p>
    </div>
  );
}

// Empty State
export function EmptyState({
  title,
  description,
  action
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-line p-8 text-center">
      <h4 className="text-base font-semibold text-ink">{title}</h4>
      <p className="mt-1 max-w-sm text-xs text-muted">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// Error Boundary
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallbackTitle?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an unhandled error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-2xl mx-auto my-12 rounded-2xl border border-fail/30 bg-fail-soft/20 text-center space-y-4 shadow-sm">
          <div className="h-12 w-12 rounded-full bg-fail/20 text-fail mx-auto flex items-center justify-center font-bold text-xl">
            !
          </div>
          <h2 className="text-lg font-bold text-ink">
            {this.props.fallbackTitle || "Something went wrong in this view"}
          </h2>
          <p className="text-xs text-muted max-w-md mx-auto">
            {this.state.error?.message || "An unexpected rendering error occurred."}
          </p>
          <div className="pt-2">
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-4 py-2 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent/90 transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

