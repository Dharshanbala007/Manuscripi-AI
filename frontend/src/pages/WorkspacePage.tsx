import { useParams } from "react-router-dom";

export function WorkspacePage() {
  const { id } = useParams();
  return <p className="text-sm text-zinc-500">Workspace for {id}…</p>;
}
