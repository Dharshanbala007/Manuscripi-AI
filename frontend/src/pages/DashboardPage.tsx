import { ArrowRight, FileText, Lock, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { EmptyState } from "../components/ui/Feedback";
import { api } from "../lib/api";
import type { ProfileSummary } from "../lib/types";

export function DashboardPage() {
  const navigate = useNavigate();
  const [formats, setFormats] = useState<ProfileSummary[]>([]);

  useEffect(() => {
    api.formats().then(setFormats).catch(() => setFormats([]));
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col items-start gap-4">
        <Badge tone="accent">
          <Sparkles className="h-3 w-3" /> Rule-based · offline-capable
        </Badge>
        <h1 className="max-w-2xl text-3xl font-semibold tracking-tight text-zinc-900">
          Turn a raw manuscript into a publication-ready document.
        </h1>
        <p className="max-w-2xl text-sm text-zinc-600">
          Upload an unformatted Word <code className="rounded bg-zinc-100 px-1">.docx</code>. ManuScript
          AI analyses its structure, applies a publisher format profile, validates the result, and
          exports a verified DOCX or PDF — all on this machine.
        </p>
        <Button onClick={() => navigate("/upload")} className="mt-1">
          New manuscript <ArrowRight className="h-4 w-4" />
        </Button>
      </section>

      <div className="grid gap-5 md:grid-cols-2">
        <Card>
          <CardHeader title="Supported publication formats" />
          <CardBody className="flex flex-col gap-3">
            {formats.length === 0 ? (
              <p className="text-xs text-zinc-500">Loading…</p>
            ) : (
              formats.map((f) => (
                <div key={f.id} className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-zinc-900">{f.name}</span>
                      <Badge tone={f.status === "available" ? "success" : "muted"}>
                        {f.status === "available" ? "Available" : "Planned"}
                      </Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-zinc-500">{f.summary}</p>
                  </div>
                </div>
              ))
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="How it works" />
          <CardBody className="flex flex-col gap-3 text-sm text-zinc-600">
            <Step icon={FileText} text="Analyse — parse the document and classify every element with a confidence score." />
            <Step icon={ShieldCheck} text="Format & validate — apply the profile, then check structure, references, and layout." />
            <Step icon={Lock} text="Private — processing runs locally; nothing is uploaded to any external service." />
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Recent manuscripts" description="Local history arrives in a later release." />
        <CardBody>
          <EmptyState
            icon={FileText}
            title="No manuscripts yet"
            description="Upload a .docx to run it through the pipeline."
            action={<Button size="sm" variant="secondary" onClick={() => navigate("/upload")}>Upload a manuscript</Button>}
          />
        </CardBody>
      </Card>
    </div>
  );
}

function Step({ icon: Icon, text }: { icon: typeof FileText; text: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" aria-hidden="true" />
      <span>{text}</span>
    </div>
  );
}
