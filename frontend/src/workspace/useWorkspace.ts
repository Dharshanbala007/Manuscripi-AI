import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "../lib/api";
import type {
  AnalysisOut,
  ChangeLogOut,
  ComparisonOut,
  ElementOut,
  FormatOut,
  HealthScoreOut,
  IssueOut,
  MetadataIn,
  MetadataOut,
  OutlineNode,
  PreservationOut,
  StatsOut,
  ValidateOut,
} from "../lib/types";

export interface WorkspaceState {
  loading: boolean;
  error: string | null;
  notFound: boolean;
  docState: string;
  filename: string;
  profileId: string | null;
  metadata: MetadataOut | null;
  stats: StatsOut | null;
  pageCount: number | null;
  outline: OutlineNode[];
  elements: ElementOut[];
  issues: IssueOut[];
  health: HealthScoreOut | null;
  changeLog: ChangeLogOut | null;
  preservation: PreservationOut | null;
  parseWarnings: string[];
  pdfExport: boolean;
  comparison: ComparisonOut | null;
  comparisonLoading: boolean;
}

const EMPTY: WorkspaceState = {
  loading: true,
  error: null,
  notFound: false,
  docState: "analyzed",
  filename: "",
  profileId: null,
  metadata: null,
  stats: null,
  pageCount: null,
  outline: [],
  elements: [],
  issues: [],
  health: null,
  changeLog: null,
  preservation: null,
  parseWarnings: [],
  pdfExport: false,
  comparison: null,
  comparisonLoading: false,
};

function applyAnalysis(prev: WorkspaceState, a: AnalysisOut): WorkspaceState {
  return {
    ...prev,
    docState: a.state,
    profileId: a.profile_id,
    metadata: a.metadata,
    stats: a.stats,
    pageCount: a.page_count,
    issues: a.issues,
    health: a.health,
    changeLog: a.change_log,
    preservation: a.preservation,
    parseWarnings: a.parse_warnings,
  };
}

export function useWorkspace(id: string) {
  const [s, setS] = useState<WorkspaceState>(EMPTY);

  const loadStructure = useCallback(async () => {
    const [outline, elements] = await Promise.all([
      api.getOutline(id).catch(() => ({ nodes: [] as OutlineNode[] })),
      api.getElements(id).catch(() => ({ items: [] as ElementOut[], total: 0, offset: 0, limit: 0 })),
    ]);
    setS((prev) => ({ ...prev, outline: outline.nodes, elements: elements.items }));
  }, [id]);

  const reload = useCallback(async () => {
    setS((prev) => ({ ...prev, loading: true, error: null, notFound: false }));
    try {
      const [doc, analysis, health] = await Promise.all([
        api.getDocument(id),
        api.getAnalysis(id),
        api.health(),
      ]);
      setS((prev) => ({
        ...applyAnalysis(prev, analysis),
        loading: false,
        error: null,
        notFound: false,
        filename: doc.filename,
        pdfExport: health.capabilities.pdf_export,
      }));
      await loadStructure();
    } catch (err) {
      const notFound = err instanceof ApiError && err.status === 404;
      setS((prev) => ({
        ...prev,
        loading: false,
        notFound,
        error: notFound
          ? "This working session has ended. Upload the document again to continue."
          : err instanceof ApiError
            ? err.message
            : "Could not load the workspace.",
      }));
    }
  }, [id, loadStructure]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const saveMetadata = useCallback(
    async (body: MetadataIn) => {
      await api.putMetadata(id, body);
      const analysis = await api.getAnalysis(id);
      setS((prev) => applyAnalysis(prev, analysis));
      await loadStructure();
    },
    [id, loadStructure],
  );

  const reclassify = useCallback(
    async (blockId: string, patch: { kind?: string; level?: number }) => {
      await api.patchElement(id, blockId, patch);
      const analysis = await api.getAnalysis(id);
      setS((prev) => applyAnalysis(prev, analysis));
      await loadStructure();
    },
    [id, loadStructure],
  );

  const applyFormat = useCallback(
    async (profileId: string): Promise<FormatOut> => {
      const result = await api.format(id, profileId);
      setS((prev) => ({
        ...prev,
        docState: result.state,
        profileId: result.profile_id,
        issues: result.issues,
        health: result.health,
        changeLog: result.change_log,
        preservation: result.preservation,
        comparison: null, // stale after re-formatting
      }));
      return result;
    },
    [id],
  );

  const runValidate = useCallback(async (): Promise<ValidateOut> => {
    const result = await api.validate(id);
    setS((prev) => ({
      ...prev,
      docState: result.state,
      issues: result.issues,
      health: result.health,
      preservation: result.preservation,
    }));
    return result;
  }, [id]);

  const loadComparison = useCallback(async () => {
    setS((prev) => ({ ...prev, comparisonLoading: true }));
    try {
      const comparison = await api.getComparison(id);
      setS((prev) => ({ ...prev, comparison, comparisonLoading: false }));
    } catch {
      setS((prev) => ({ ...prev, comparisonLoading: false }));
    }
  }, [id]);

  return {
    ...s,
    reload,
    saveMetadata,
    reclassify,
    applyFormat,
    runValidate,
    loadComparison,
  };
}
