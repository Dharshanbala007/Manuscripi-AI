import { ArrowLeft, ArrowRight, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card, CardBody } from "../components/ui/Card";
import { Spinner } from "../components/ui/Feedback";
import { useToast } from "../components/ui/Toast";
import { Dropzone } from "../components/upload/Dropzone";
import { ApiError, api } from "../lib/api";
import { humanBytes } from "../lib/format";
import type { DocumentOut } from "../lib/types";
import { useDocumentFlow } from "../state/useDocumentFlow";

const MAX_MB = 25;

export function UploadPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const flow = useDocumentFlow();
  const [doc, setDoc] = useState<DocumentOut | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (flow.state === "IDLE") flow.goto("UPLOADING");
  }, [flow.state, flow.goto]);

  async function handleAccept(file: File) {
    setBusy(true);
    try {
      const uploaded = await api.upload(file);
      setDoc(uploaded);
      flow.goto("UPLOADED", { documentId: uploaded.id });
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Upload failed. Please try again.";
      toast.error(message);
      flow.goto("ERROR", { error: message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6">
      <Link to="/" className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-800">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to dashboard
      </Link>

      <div>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-900">Upload a manuscript</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Word <code className="rounded bg-zinc-100 px-1">.docx</code> only, up to {MAX_MB} MB. The
          original file is never modified.
        </p>
      </div>

      {doc ? (
        <Card>
          <CardBody className="flex items-center gap-4">
            <span className="grid h-10 w-10 place-items-center rounded-lg bg-accent text-primary">
              <FileText className="h-5 w-5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-zinc-900">{doc.filename}</p>
              <p className="text-xs text-zinc-500">
                {humanBytes(doc.size)} · uploaded
              </p>
            </div>
            <Button
              onClick={() => {
                flow.goto("ANALYZING");
                navigate(`/analyze/${doc.id}`);
              }}
            >
              Analyse manuscript <ArrowRight className="h-4 w-4" />
            </Button>
          </CardBody>
        </Card>
      ) : (
        <div className="relative">
          <Dropzone onAccept={handleAccept} maxMb={MAX_MB} disabled={busy} />
          {busy ? (
            <div className="absolute inset-0 grid place-items-center rounded-2xl bg-white/70">
              <span className="inline-flex items-center gap-2 text-sm text-zinc-600">
                <Spinner /> Uploading…
              </span>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
