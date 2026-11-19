import { forwardRef, type ButtonHTMLAttributes, type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { CONFIDENCE_META, VERDICT_META } from "@/lib/utils";
import type { Confidence, Verdict } from "@/lib/types";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "dark" | "coral";
type ButtonSize = "sm" | "md" | "lg";

const VARIANTS: Record<ButtonVariant, string> = {
  primary:
    "border-2 border-ink bg-violet text-white shadow-block-sm hover:bg-violet-deep hover:-translate-x-[1px] hover:-translate-y-[1px] hover:shadow-block active:translate-x-[1px] active:translate-y-[1px] active:shadow-none",
  secondary:
    "border-2 border-ink bg-lavender text-ink shadow-block-sm hover:bg-[#cec5ff] hover:-translate-x-[1px] hover:-translate-y-[1px] hover:shadow-block active:translate-x-[1px] active:translate-y-[1px] active:shadow-none",
  outline:
    "border-2 border-ink bg-white text-ink hover:bg-lavender-soft hover:-translate-x-[1px] hover:-translate-y-[1px] hover:shadow-block-sm active:translate-x-[1px] active:translate-y-[1px] active:shadow-none",
  ghost: "border-2 border-transparent bg-transparent text-ink/70 hover:border-ink/15 hover:bg-lavender-soft hover:text-ink",
  dark: "border-2 border-ink bg-ink text-white shadow-block-sm hover:bg-[#241f47] hover:-translate-x-[1px] hover:-translate-y-[1px] hover:shadow-block active:translate-x-[1px] active:translate-y-[1px] active:shadow-none",
  coral:
    "border-2 border-ink bg-coral text-white shadow-block-sm hover:bg-[#f05a33] hover:-translate-x-[1px] hover:-translate-y-[1px] hover:shadow-block active:translate-x-[1px] active:translate-y-[1px] active:shadow-none",
};

const SIZES: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-[11px] gap-1.5",
  md: "h-11 px-5 text-sm gap-2",
  lg: "h-12 px-6 text-[15px] gap-2",
};

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize }
>(({ className, variant = "primary", size = "md", ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "inline-flex select-none items-center justify-center rounded-md font-bold uppercase tracking-[0.02em] transition-all duration-150",
      "disabled:pointer-events-none disabled:opacity-50",
      VARIANTS[variant],
      SIZES[size],
      className,
    )}
    {...props}
  />
));
Button.displayName = "Button";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("block-card", className)} {...props} />;
}

export function Badge({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm bg-paper px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.08em] text-slate",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function VerdictBadge({
  verdict,
  size = "md",
  className,
}: {
  verdict: Verdict | null | undefined;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const meta = VERDICT_META[verdict ?? "insufficient_evidence"];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm font-semibold",
        size === "sm" && "px-2 py-0.5 text-[10.5px]",
        size === "md" && "px-2.5 py-1 text-[11.5px]",
        size === "lg" && "px-3 py-1.5 text-[13px]",
        meta.className,
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", meta.dot)} />
      {meta.label}
    </span>
  );
}

export function ConfidenceMeter({
  level,
  reason,
  className,
}: {
  level: Confidence | null | undefined;
  reason?: string;
  className?: string;
}) {
  const value = level ?? "low";
  const meta = CONFIDENCE_META[value];
  return (
    <div className={cn("flex items-center gap-1.5", className)} title={reason}>
      <div className="flex items-end gap-[2px]" aria-hidden>
        {[1, 2, 3].map((bar) => (
          <span
            key={bar}
            className={cn(
              "w-[4px] rounded-sm",
              bar === 1 && "h-1.5",
              bar === 2 && "h-2.5",
              bar === 3 && "h-3.5",
              bar <= meta.bars ? "bg-violet" : "bg-line",
            )}
          />
        ))}
      </div>
      <span className="text-[10.5px] text-slate">{meta.label.replace(" confidence", "")}</span>
      {reason ? <span className="sr-only">{reason}</span> : null}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn("inline-block h-4 w-4 animate-spin rounded-full border-2 border-ink/20 border-t-ink", className)}
      role="status"
      aria-label="Loading"
    />
  );
}

export function SectionLabel({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("label-mono", className)}>{children}</p>;
}

export function StatTile({
  value,
  label,
  hint,
  tone = "white",
}: {
  value: ReactNode;
  label: string;
  hint?: string;
  tone?: "white" | "lavender" | "violet" | "coral" | "mint" | "ink";
}) {
  const tones: Record<string, string> = {
    white: "bg-white text-ink",
    lavender: "bg-lavender-soft text-ink",
    violet: "bg-violet text-white",
    coral: "bg-coral text-white",
    mint: "bg-mint text-ink",
    ink: "bg-ink text-white",
  };
  return (
    <div className={cn("flex flex-col gap-1 border-2 border-ink p-4", tones[tone])}>
      <span className="font-display text-2xl leading-none">{value}</span>
      <p className="text-[12px] font-semibold">{label}</p>
      {hint ? <p className="text-[11px] text-slate">{hint}</p> : null}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 border-2 border-dashed border-ink/40 bg-white/70 px-6 py-14 text-center">
      <p className="display text-lg">{title}</p>
      <p className="max-w-md text-sm leading-relaxed text-slate">{description}</p>
      {action}
    </div>
  );
}

export function ProgressBar({ value, tone = "violet" }: { value: number; tone?: "violet" | "coral" }) {
  return (
    <div className="h-2.5 w-full overflow-hidden border-2 border-ink bg-white">
      <div
        className={cn("h-full transition-all duration-500", tone === "violet" ? "bg-violet" : "bg-coral")}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}
