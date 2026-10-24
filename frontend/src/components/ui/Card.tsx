import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  strong?: boolean;
  hover?: boolean;
}

export function Card({ children, strong, hover, className, ...rest }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl",
        strong ? "glass-strong" : "glass",
        "shadow-card",
        hover && "transition hover:border-white/20 hover:shadow-glow",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
