import { Download, FileText } from "lucide-react";
import { useState } from "react";

import { api } from "../../lib/api";
import { useToast } from "../ui/Toast";
import { Button } from "../ui/Button";

async function downloadFile(url: string, filename: string): Promise<void> {
  const res = await fetch(url);
  if (!res.ok) {
    let message = "Export failed.";
    try {
      const body = (await res.json()) as { message?: string };
      message = body.message ?? message;
    } catch {
      /* non-JSON */
    }
    throw new Error(message);
  }
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

export function ExportBar({
  docId,
  profileId,
  ready,
  pdfExport,
}: {
  docId: string;
  profileId: string | null;
  ready: boolean;
  pdfExport: boolean;
}) {
  const toast = useToast();
  const [busy, setBusy] = useState<"docx" | "pdf" | null>(null);
  const base = `manuscript_${profileId ?? "ieee"}_formatted`;

  async function run(kind: "docx" | "pdf") {
    setBusy(kind);
    try {
      await downloadFile(
        kind === "docx" ? api.exportDocxUrl(docId) : api.exportPdfUrl(docId),
        `${base}.${kind}`,
      );
      toast.success(`${kind.toUpperCase()} exported.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button onClick={() => run("docx")} disabled={!ready} loading={busy === "docx"}>
        <FileText className="h-4 w-4" /> Export DOCX
      </Button>
      <Button
        variant="secondary"
        onClick={() => run("pdf")}
        disabled={!ready || !pdfExport}
        loading={busy === "pdf"}
        title={pdfExport ? undefined : "PDF export needs LibreOffice on the server"}
      >
        <Download className="h-4 w-4" /> Export PDF
      </Button>
      {!pdfExport ? (
        <span className="text-xs text-zinc-500">PDF export unavailable on this machine.</span>
      ) : null}
    </div>
  );
}
