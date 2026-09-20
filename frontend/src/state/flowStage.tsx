import { type ReactNode, createContext, useContext, useMemo, useState } from "react";

// Which step of the flow rail the workspace is on. Upload/Analyze come from the route;
// once in the workspace the page reports Review / Format / Export here.
export const STEPS = ["Upload", "Analyze", "Review", "Format", "Export"] as const;

export function stageForDocState(docState: string): number {
  if (docState === "exported") return 4;
  if (docState === "formatted" || docState === "validated") return 3;
  return 2;
}

interface FlowStage {
  workspaceStage: number | null;
  setWorkspaceStage: (stage: number | null) => void;
}

// Components rendered outside the provider (unit tests) get a harmless no-op.
const FlowStageContext = createContext<FlowStage>({
  workspaceStage: null,
  setWorkspaceStage: () => undefined,
});

export function FlowStageProvider({ children }: { children: ReactNode }) {
  const [workspaceStage, setWorkspaceStage] = useState<number | null>(null);
  const value = useMemo(() => ({ workspaceStage, setWorkspaceStage }), [workspaceStage]);
  return <FlowStageContext.Provider value={value}>{children}</FlowStageContext.Provider>;
}

export function useFlowStage(): FlowStage {
  return useContext(FlowStageContext);
}
