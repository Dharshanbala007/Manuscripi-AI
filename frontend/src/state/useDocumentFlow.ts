import { useCallback, useEffect, useReducer } from "react";

import type { ProcessingState } from "../lib/types";

/**
 * The document-processing state machine. One reducer, explicit transitions.
 * No status strings scattered through the UI.
 */
const TRANSITIONS: Record<ProcessingState, ProcessingState[]> = {
  IDLE: ["UPLOADING"],
  UPLOADING: ["UPLOADED", "ERROR", "IDLE"],
  UPLOADED: ["ANALYZING", "IDLE"],
  ANALYZING: ["ANALYZED", "ERROR"],
  ANALYZED: ["REVIEWING", "FORMATTING", "ANALYZING", "IDLE"],
  REVIEWING: ["FORMATTING", "ANALYZING", "IDLE"],
  FORMATTING: ["FORMATTED", "ERROR"],
  FORMATTED: ["VALIDATING", "FORMATTING", "REVIEWING", "EXPORTING", "IDLE"],
  VALIDATING: ["VALIDATED", "ERROR"],
  VALIDATED: ["EXPORTING", "FORMATTING", "REVIEWING", "IDLE"],
  EXPORTING: ["EXPORTED", "ERROR", "FORMATTED", "VALIDATED"],
  EXPORTED: ["EXPORTING", "FORMATTING", "REVIEWING", "IDLE"],
  ERROR: ["IDLE", "UPLOADING", "ANALYZING", "FORMATTING", "VALIDATING", "EXPORTING"],
};

const STORAGE_KEY = "manuscript-ai:flow";

export interface FlowSnapshot {
  state: ProcessingState;
  documentId: string | null;
  error: string | null;
}

type Action =
  | { type: "reset" }
  | { type: "goto"; to: ProcessingState; documentId?: string | null; error?: string | null };

function reducer(current: FlowSnapshot, action: Action): FlowSnapshot {
  if (action.type === "reset") {
    return { state: "IDLE", documentId: null, error: null };
  }
  const allowed = TRANSITIONS[current.state] ?? [];
  if (!allowed.includes(action.to)) return current; // illegal transition: no-op

  return {
    state: action.to,
    documentId:
      action.documentId !== undefined ? action.documentId : current.documentId,
    error: action.to === "ERROR" ? action.error ?? "Something went wrong." : null,
  };
}

function initialSnapshot(): FlowSnapshot {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<FlowSnapshot>;
      if (typeof parsed.state === "string" && parsed.state in TRANSITIONS) {
        return {
          state: parsed.state as ProcessingState,
          documentId: parsed.documentId ?? null,
          error: null,
        };
      }
    }
  } catch {
    /* private mode / cleared storage / stale value */
  }
  return { state: "IDLE", documentId: null, error: null };
}

export function canTransition(from: ProcessingState, to: ProcessingState): boolean {
  return (TRANSITIONS[from] ?? []).includes(to);
}

export function useDocumentFlow() {
  const [snapshot, dispatch] = useReducer(reducer, undefined, initialSnapshot);

  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ state: snapshot.state, documentId: snapshot.documentId }),
      );
    } catch {
      /* ignore */
    }
  }, [snapshot.state, snapshot.documentId]);

  const goto = useCallback(
    (to: ProcessingState, opts?: { documentId?: string | null; error?: string | null }) =>
      dispatch({ type: "goto", to, ...opts }),
    [],
  );
  const reset = useCallback(() => dispatch({ type: "reset" }), []);

  return { ...snapshot, goto, reset };
}
