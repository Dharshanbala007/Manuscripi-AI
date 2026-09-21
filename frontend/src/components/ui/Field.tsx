import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";
import { useId } from "react";

import { cn } from "../../lib/cn";

const CONTROL =
  "w-full rounded-lg border border-input bg-card/80 px-3 py-2 text-sm text-foreground transition-[border-color,box-shadow] " +
  "placeholder:text-muted-foreground focus:border-primary focus:bg-card focus:shadow-[0_0_0_4px_hsl(var(--primary)/0.12)] focus:outline-none disabled:bg-secondary";

function Wrapper({
  label,
  hint,
  htmlFor,
  children,
}: {
  label?: ReactNode;
  hint?: ReactNode;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      {label ? (
        <label htmlFor={htmlFor} className="flex items-center gap-2 text-xs font-medium text-foreground">
          {label}
        </label>
      ) : null}
      {children}
      {hint ? <p className="text-[11px] text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function TextField({
  label,
  hint,
  className,
  id,
  ...rest
}: InputHTMLAttributes<HTMLInputElement> & { label?: ReactNode; hint?: ReactNode }) {
  const generated = useId();
  const fieldId = id ?? generated;
  return (
    <Wrapper label={label} hint={hint} htmlFor={fieldId}>
      <input id={fieldId} className={cn(CONTROL, className)} {...rest} />
    </Wrapper>
  );
}

export function TextArea({
  label,
  hint,
  className,
  id,
  ...rest
}: TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: ReactNode; hint?: ReactNode }) {
  const generated = useId();
  const fieldId = id ?? generated;
  return (
    <Wrapper label={label} hint={hint} htmlFor={fieldId}>
      <textarea id={fieldId} className={cn(CONTROL, "min-h-[6rem] resize-y", className)} {...rest} />
    </Wrapper>
  );
}
