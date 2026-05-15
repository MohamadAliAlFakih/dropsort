import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "muted";
  children: ReactNode;
};

export function Button({
  variant = "primary",
  className = "",
  type = "button",
  children,
  ...rest
}: ButtonProps) {
  const variantClass = variant === "muted" ? "btn-muted" : "btn-primary";
  const classes = ["btn", variantClass, className].filter(Boolean).join(" ");
  return (
    <button type={type} className={classes} {...rest}>
      {children}
    </button>
  );
}
