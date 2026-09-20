import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { StageSurface } from "../components/layout/StageSurface";
import { ComparePanel } from "../components/workspace/ComparePanel";
import { ElementsList } from "../components/workspace/ElementsList";
import { ExportBar } from "../components/workspace/ExportBar";
import { FormatPicker } from "../components/workspace/FormatPicker";
import { HealthCard } from "../components/workspace/HealthCard";
import { IssuesPanel } from "../components/workspace/IssuesPanel";
import { MetadataEditor } from "../components/workspace/MetadataEditor";
import { OutlinePanel } from "../components/workspace/OutlinePanel";
import { PreviewPane } from "../components/workspace/PreviewPane";
import { StatsPanel } from "../components/workspace/StatsPanel";
import { TopBar } from "../components/workspace/TopBar";
import { WhatChanged } from "../components/workspace/WhatChanged";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { ErrorState, Spinner } from "../components/ui/Feedback";
import { Tabs } from "../components/ui/Tabs";
import { useToast } from "../components/ui/Toast";
import { ApiError } from "../lib/api";
import { stageForDocState, useFlowStage } from "../state/flowStage";
import { useDocumentFlow } from "../state/useDocumentFlow";
import { useWorkspace } from "../workspace/useWorkspace";

type CenterTab = "review" | "preview" | "changes" | "compare";

const FORMATTED_STATES = ["formatted", "validated", "exported"];

export function WorkspacePage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { goto } = useDocumentFlow();
  const ws = useWorkspace(id);
  const { setWorkspaceStage } = useFlowStage();

  useEffect(() => {
    setWorkspaceStage(stageForDocState(ws.docState));
    return () => setWorkspaceStage(null);
  }, [ws.docState, setWorkspaceStage]);

  const [formatOpen, setFormatOpen] = useState(false);
  const [centerTab, setCenterTab] = useState<CenterTab>("review");
  const [drawer, setDrawer] = useState<null | "outline" | "issues">(null);

  const formatted = FORMATTED_STATES.includes(ws.docState);

  function locate(blockId: string) {
    setCenterTab("review");
    setDrawer(null);
    requestAnimationFrame(() => {
      document
        .querySelector(`[data-block-id="${blockId}"]`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  function openCompare() {
    setCenterTab("compare");
    if (!ws.comparison && formatted) void ws.loadComparison();
  }

  async function applyFormat(profileId: string) {
    goto("FORMATTING");
    try {
      const result = await ws.applyFormat(profileId);
      goto("FORMATTED");
      toast.success(`${profileId.toUpperCase()} format profile applied.`);
      setCenterTab("changes");
      if (result.preservation && !result.preservation.passed) {
        toast.error("Content review required — see What changed.");
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Formatting failed.";
      goto("ERROR", { error: message });
      toast.error(message);
      throw err;
    }
  }

  async function validate() {
    goto("VALIDATING");
    try {
      await ws.runValidate();
      goto("VALIDATED");
      toast.success("Validation checks completed.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Validation failed.");
      throw err;
    }
  }

  if (ws.loading) {
    // Mount the shared surface in the same commit as the route change so it can morph
    // out of the previous screen's surface; the header fills in once data arrives.
    return (
      <StageSurface radius={20} className="px-5 py-3.5">
        <div role="status" className="flex h-[34px] items-center gap-2.5 text-sm text-zinc-600">
          <Spinner className="h-4 w-4 text-primary" /> Loading workspace…
        </div>
      </StageSurface>
    );
  }

  if (ws.error) {
    return (
      <ErrorState
        title={ws.notFound ? "Session ended" : "Could not load the workspace"}
        description={ws.error}
        action={<Button onClick={() => navigate(ws.notFound ? "/upload" : "/")}>
          {ws.notFound ? "Upload a manuscript" : "Back to dashboard"}
        </Button>}
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <StageSurface radius={20} className="px-5 py-3.5">
        <TopBar
          filename={ws.filename}
          docState={ws.docState}
          profileId={ws.profileId}
          healthTotal={ws.health?.total ?? null}
          formatOpen={formatOpen}
          onOpenFormat={() => setFormatOpen(true)}
          onValidate={validate}
        />
      </StageSurface>

      <div className="flex gap-2 lg:hidden">
        <Button size="sm" variant="secondary" onClick={() => setDrawer("outline")}>
          Outline
        </Button>
        <Button size="sm" variant="secondary" onClick={() => setDrawer("issues")}>
          Issues ({ws.issues.length})
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[15rem_minmax(0,1fr)_20rem]">
        <aside className="hidden lg:block">
          <OutlinePanel nodes={ws.outline} onLocate={locate} />
        </aside>

        <div className="flex flex-col gap-4">
          <Tabs
            active={centerTab}
            onChange={(t) => (t === "compare" ? openCompare() : setCenterTab(t as CenterTab))}
            items={[
              { id: "review", label: "Review" },
              { id: "preview", label: "Preview" },
              { id: "changes", label: "What changed" },
              { id: "compare", label: "Compare" },
            ]}
          />

          {centerTab === "review" && ws.metadata ? (
            <>
              {ws.stats ? <StatsPanel stats={ws.stats} pageCount={ws.pageCount} /> : null}
              <MetadataEditor metadata={ws.metadata} onSave={ws.saveMetadata} />
              <ElementsList elements={ws.elements} onReclassify={ws.reclassify} />
            </>
          ) : null}

          {centerTab === "preview" ? <PreviewPane docId={id} ready={formatted} /> : null}

          {centerTab === "changes" ? (
            <>
              <WhatChanged changeLog={ws.changeLog} preservation={ws.preservation} />
              {formatted ? (
                <Card>
                  <CardHeader title="Export" description="Verified files, generated locally." />
                  <CardBody>
                    <ExportBar
                      docId={id}
                      profileId={ws.profileId}
                      ready={formatted}
                      pdfExport={ws.pdfExport}
                    />
                  </CardBody>
                </Card>
              ) : null}
            </>
          ) : null}

          {centerTab === "compare" ? (
            <ComparePanel
              comparison={ws.comparison}
              loading={ws.comparisonLoading}
              ready={formatted}
              onLoad={ws.loadComparison}
            />
          ) : null}
        </div>

        <aside className="hidden flex-col gap-4 lg:flex">
          <HealthCard health={ws.health} />
          <IssuesPanel issues={ws.issues} onLocate={locate} />
        </aside>
      </div>

      {drawer ? (
        <div
          className="fixed inset-0 z-50 bg-zinc-900/40 lg:hidden"
          onMouseDown={(e) => e.target === e.currentTarget && setDrawer(null)}
        >
          <div className="absolute right-0 top-0 h-full w-[20rem] max-w-[85vw] overflow-y-auto bg-white p-4 shadow-raised">
            {drawer === "outline" ? (
              <OutlinePanel nodes={ws.outline} onLocate={locate} />
            ) : (
              <div className="flex flex-col gap-4">
                <HealthCard health={ws.health} />
                <IssuesPanel issues={ws.issues} onLocate={locate} />
              </div>
            )}
          </div>
        </div>
      ) : null}

      <FormatPicker
        open={formatOpen}
        onClose={() => setFormatOpen(false)}
        currentProfile={ws.profileId}
        onApply={applyFormat}
      />
    </div>
  );
}
