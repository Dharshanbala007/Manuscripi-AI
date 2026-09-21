import { motion } from "motion/react";
import { FileText, Lock, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { RecentList } from "../components/dashboard/RecentList";
import { Badge } from "../components/ui/Badge";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { FlowButton } from "../components/ui/FlowButton";
import { api } from "../lib/api";
import type { ProfileSummary } from "../lib/types";

const STAGGER = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const RISE = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 260, damping: 28 } },
} as const;

export function DashboardPage() {
  const navigate = useNavigate();
  const [formats, setFormats] = useState<ProfileSummary[]>([]);

  useEffect(() => {
    api.formats().then(setFormats).catch(() => setFormats([]));
  }, []);

  return (
    <motion.div className="flex flex-col gap-8" variants={STAGGER} initial="hidden" animate="show">
      <motion.section variants={RISE} className="flex flex-col items-start gap-4">
        <Badge tone="accent">
          <Sparkles className="h-3 w-3" /> Rule-based · offline-capable
        </Badge>
        <h1 className="max-w-2xl text-4xl font-semibold leading-[1.1] tracking-tight text-foreground">
          Turn a raw manuscript into a{" "}
          <span className="relative whitespace-nowrap">
            publication-ready
            <span
              aria-hidden="true"
              className="absolute inset-x-0 bottom-0.5 -z-10 h-2.5 rounded-full bg-gradient-to-r from-primary/30 to-violet-400/30"
            />
          </span>{" "}
          document.
        </h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Upload an unformatted Word{" "}
          <code className="rounded bg-secondary px-1 text-foreground">.docx</code>. ManuScript AI
          analyses its structure, applies a publisher format profile, validates the result, and
          exports a verified DOCX or PDF — all on this machine.
        </p>
        <FlowButton text="New manuscript" onClick={() => navigate("/upload")} className="mt-1" />
      </motion.section>

      <motion.div variants={RISE} className="grid gap-5 md:grid-cols-2">
        <Card>
          <CardHeader title="Supported publication formats" />
          <CardBody className="flex flex-col gap-3">
            {formats.length === 0 ? (
              <p className="text-xs text-muted-foreground">Loading…</p>
            ) : (
              formats.map((f) => (
                <div key={f.id} className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground">{f.name}</span>
                      <Badge tone={f.status === "available" ? "success" : "muted"}>
                        {f.status === "available" ? "Available" : "Planned"}
                      </Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">{f.summary}</p>
                  </div>
                </div>
              ))
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="How it works" />
          <CardBody className="flex flex-col gap-3 text-sm text-muted-foreground">
            <Step icon={FileText} text="Analyse — parse the document and classify every element with a confidence score." />
            <Step icon={ShieldCheck} text="Format & validate — apply the profile, then check structure, references, and layout." />
            <Step icon={Lock} text="Private — processing runs locally; nothing is uploaded to any external service." />
          </CardBody>
        </Card>
      </motion.div>

      <motion.div variants={RISE}>
        <Card>
          <CardHeader
            title="Recent manuscripts"
            description="Local history — stored on this machine, no manuscript content."
          />
          <CardBody>
            <RecentList />
          </CardBody>
        </Card>
      </motion.div>
    </motion.div>
  );
}

function Step({ icon: Icon, text }: { icon: typeof FileText; text: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
      <span>{text}</span>
    </div>
  );
}
