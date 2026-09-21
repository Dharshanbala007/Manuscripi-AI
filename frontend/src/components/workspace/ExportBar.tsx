import { Download, FileText } from "lucide-react";

import { api } from "../../lib/api";
import { useFlowStage } from "../../state/flowStage";
import { useToast } from "../ui/Toast";
import { MorphButton } from "../ui/MorphButton";

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
  const { setWorkspaceStage } = useFlowStage();
  const base = `manuscript_${profileId ?? "ieee"}_formatted`;

  async function run(kind: "docx" | "pdf") {
    try {
      await downloadFile(
        kind === "docx" ? api.exportDocxUrl(docId) : api.exportPdfUrl(docId),
        `${base}.${kind}`,
      );
      toast.success(`${kind.toUpperCase()} exported.`);
      setWorkspaceStage(4);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Export failed.");
      throw err;
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <MorphButton
        variant="primary"
        icon={<FileText className="h-3.5 w-3.5" aria-hidden="true" />}
        disabled={!ready}
        pendingLabel="Exporting…"
        successLabel="Exported"
        onAction={() => run("docx")}
      >
        Export DOCX
      </MorphButton>
      <MorphButton
        icon={<Download className="h-3.5 w-3.5" aria-hidden="true" />}
        disabled={!ready || !pdfExport}
        title={pdfExport ? undefined : "PDF export needs LibreOffice on the server"}
        pendingLabel="Exporting…"
        successLabel="Exported"
        onAction={() => run("pdf")}
      >
        Export PDF
      </MorphButton>
      {!pdfExport ? (
        <span className="text-xs text-zinc-500 dark:text-zinc-400">PDF export unavailable on this machine.</span>
      ) : null}
    </div>
  );
}
