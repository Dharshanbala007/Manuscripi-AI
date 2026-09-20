import { motion } from "motion/react";
import { UploadCloud } from "lucide-react";
import { type DragEvent, useId, useRef, useState } from "react";

import { cn } from "../../lib/cn";
import { humanBytes } from "../../lib/format";

export function validateManuscriptFile(
  file: File,
  maxMb: number,
): { ok: true } | { ok: false; message: string } {
  const name = file.name.toLowerCase();
  if (!name.endsWith(".docx")) {
    return { ok: false, message: "That is not a .docx file. Upload a Word .docx manuscript." };
  }
  if (file.size > maxMb * 1024 * 1024) {
    return {
      ok: false,
      message: `That file (${humanBytes(file.size)}) is larger than the ${maxMb} MB limit.`,
    };
  }
  if (file.size === 0) {
    return { ok: false, message: "That file is empty." };
  }
  return { ok: true };
}

export function Dropzone({
  onAccept,
  maxMb,
  disabled = false,
}: {
  onAccept: (file: File) => void;
  maxMb: number;
  disabled?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFiles(files: FileList | null) {
    setError(null);
    const file = files?.[0];
    if (!file) return;
    const result = validateManuscriptFile(file, maxMb);
    if (result.ok) {
      onAccept(file);
    } else {
      setError(result.message);
    }
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div className="flex flex-col gap-3">
      <label
        htmlFor={inputId}
        data-testid="dropzone"
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "group flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-all duration-200",
          disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
          dragging
            ? "scale-[1.015] border-primary bg-accent shadow-[0_0_0_6px_hsl(var(--primary)/0.10)]"
            : "border-primary/30 bg-white/50 hover:border-primary/60 hover:bg-white/80",
        )}
      >
        <motion.span
          aria-hidden="true"
          className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-accent to-white text-primary shadow-glass"
          animate={{ y: dragging ? -6 : [0, -4, 0] }}
          transition={
            dragging
              ? { type: "spring", stiffness: 400, damping: 20 }
              : { repeat: Infinity, duration: 2.6, ease: "easeInOut" }
          }
        >
          <UploadCloud className="h-5 w-5" />
        </motion.span>
        <div>
          <p className="text-sm font-medium text-zinc-800">Drop your manuscript here</p>
          <p className="mt-0.5 text-xs text-zinc-500">Upload a .DOCX file to begin</p>
        </div>
        <span className="rounded-[9px] border border-border bg-white px-3 py-1.5 text-xs font-medium text-zinc-800 shadow-sm transition-colors group-hover:bg-zinc-50">
          Browse files
        </span>
        <input
          ref={inputRef}
          id={inputId}
          data-testid="dropzone-input"
          type="file"
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="sr-only"
          onChange={(e) => handleFiles(e.target.files)}
          disabled={disabled}
        />
      </label>
      {error ? (
        <p role="alert" className="text-xs text-red-600">
          {error}{" "}
          <button
            type="button"
            className="font-medium underline"
            onClick={() => {
              setError(null);
              inputRef.current?.click();
            }}
          >
            Try another file
          </button>
        </p>
      ) : null}
    </div>
  );
}
