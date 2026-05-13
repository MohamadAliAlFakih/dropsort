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
  return (
    <button
      type={type}
      className={["btn", variantClass, className].filter(Boolean).join(" ")}
      {...rest}
    >
      {children}
    </button>
  );
}