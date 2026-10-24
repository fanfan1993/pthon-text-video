import { forwardRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "ghost" | "outline" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
}

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-accent-gradient text-white shadow-glow hover:brightness-110 active:brightness-95",
  ghost: "text-slate-200 hover:bg-white/5",
  outline: "border border-white/15 text-slate-100 hover:bg-white/5",
  danger: "bg-rose-500/90 text-white hover:bg-rose-500",
};

const SIZES: Record<Size, string> = {
  sm: "h-9 px-3 text-sm gap-1.5",
  md: "h-11 px-5 text-sm gap-2",
  lg: "h-12 px-6 text-base gap-2",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, icon, className, children, disabled, ...rest }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-medium transition",
        "focus-ring disabled:opacity-50 disabled:cursor-not-allowed select-none",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...rest}
    >
      {loading ? (
        <span className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white animate-spin" />
      ) : (
        icon
      )}
      {children}
    </button>
  ),
);
Button.displayName = "Button";
