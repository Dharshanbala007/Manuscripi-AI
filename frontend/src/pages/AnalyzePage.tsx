import { useParams } from "react-router-dom";

export function AnalyzePage() {
  const { id } = useParams();
  return <p className="text-sm text-zinc-500">Analysing {id}…</p>;
}
