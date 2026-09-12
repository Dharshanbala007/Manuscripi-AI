import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { StageList, pendingStages } from "../components/analyze/StageList";
import { Button } from "../components/ui/Button";
import { Card, CardBody } from "../components/ui/Card";
import { ErrorState } from "../components/ui/Feedback";
import { usePolling } from "../hooks/usePolling";
import { ApiError, api } from "../lib/api";
import type { StatsOut } from "../lib/types";
import { useDocumentFlow } from "../state/useDocumentFlow";

export function AnalyzePage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { goto } = useDocumentFlow();

  const startedRef = useRef(false);
  const finishedRef = useRef(false);
  const [phase, setPhase] = useState<"working" | "error">("working");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    api.analyze(id).catch((err) => {
      // 409 == already analysing; that is fine, keep polling.
      if (err instanceof ApiError && err.status === 409) return;
      setPhase("error");
      setErrorMsg(err instanceof ApiError ? err.message : "Analysis could not be started.");
    });
  }, [id]);

  const { data, error } = usePolling(() => api.getAnalysis(id), {
    intervalMs: 400,
    enabled: phase === "working",
    stopWhen: (a) => a.state === "analyzed" || a.state === "error",
  });

  useEffect(() => {
    if (!data || finishedRef.current) return;
    if (data.state === "analyzed") {
      finishedRef.current = true;
      goto("ANALYZED", { documentId: id });
      navigate(`/workspace/${id}`, { replace: true });
    } else if (data.state === "error") {
      finishedRef.current = true;
      setPhase("error");
      setErrorMsg(data.error ?? "Some document elements could not be interpreted.");
      goto("ERROR", { error: data.error ?? "Analysis failed." });
    }
  }, [data, id, navigate, goto]);

  useEffect(() => {
    if (error && !finishedRef.current) {
      setPhase("error");
      setErrorMsg("Lost contact with the backend during analysis.");
    }
  }, [error]);

  function retry() {
    startedRef.current = false;
    finishedRef.current = false;
    setErrorMsg("");
    setPhase("working");
    api.analyze(id).catch(() => undefined);
  }

  if (phase === "error") {
    return (
      <div className="mx-auto max-w-xl">
        <ErrorState
          title="Analysis failed"
          description={errorMsg}
          action={<Button onClick={retry}>Try again</Button>}
        />
      </div>
    );
  }

  const stages = data?.stages?.length ? data.stages : pendingStages();

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-900">Analysing manuscript</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Reading the document and detecting its structure. This runs locally on your machine.
        </p>
      </div>

      <Card>
        <CardBody>
          <StageList stages={stages} />
        </CardBody>
      </Card>

      {data?.stats ? <StatsRow stats={data.stats} /> : null}
    </div>
  );
}

function StatsRow({ stats }: { stats: StatsOut }) {
  const items: [string, number][] = [
    ["Paragraphs", stats.paragraphs],
    ["Headings", stats.headings],
    ["Tables", stats.tables],
    ["Figures", stats.figures],
    ["References", stats.references],
  ];
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-center">
          <div className="text-lg font-semibold tabular-nums text-zinc-900">{value}</div>
          <div className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</div>
        </div>
      ))}
    </div>
  );
}
