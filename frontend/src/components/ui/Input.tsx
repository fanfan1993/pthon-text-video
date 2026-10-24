import { forwardRef } from "react";
import type {
  InputHTMLAttributes,
  TextareaHTMLAttributes,
  SelectHTMLAttributes,
  ReactNode,
} from "react";
import { cn } from "@/lib/cn";

const base =
  "w-full rounded-xl bg-white/[0.03] border border-white/10 px-3.5 py-2.5 text-[15px] text-slate-100 " +
  "placeholder:text-slate-500 focus-ring transition";

interface FieldProps {
  label?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

export function Field({ label, hint, error, children }: FieldProps) {
  return (
    <label className="block space-y-1.5">
      {label && (
        <span className="text-sm font-medium text-slate-300">{label}</span>
      )}
      {children}
      {hint && !error && <span className="text-xs text-slate-500">{hint}</span>}
      {error && <span className="text-xs text-rose-400">{error}</span>}
    </label>
  );
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...rest }, ref) => (
    <input ref={ref} className={cn(base, "h-11", className)} {...rest} />
  ),
);
Input.displayName = "Input";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...rest }, ref) => (
  <textarea ref={ref} className={cn(base, "min-h-[96px] resize-y leading-relaxed", className)} {...rest} />
));
Textarea.displayName = "Textarea";

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...rest }, ref) => (
  <select ref={ref} className={cn(base, "h-11 appearance-none cursor-pointer", className)} {...rest}>
    {children}
  </select>
));
Select.displayName = "Select";
