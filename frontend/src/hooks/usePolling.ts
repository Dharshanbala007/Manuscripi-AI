import { useEffect, useRef, useState } from "react";

/**
 * Repeatedly call `fn` every `intervalMs` while `enabled` and `stopWhen(result)`
 * is false. The latest result and any thrown error are returned.
 */
export function usePolling<T>(
  fn: () => Promise<T>,
  {
    intervalMs = 400,
    enabled = true,
    stopWhen = () => false,
  }: { intervalMs?: number; enabled?: boolean; stopWhen?: (result: T) => boolean } = {},
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const fnRef = useRef(fn);
  const stopRef = useRef(stopWhen);
  fnRef.current = fn;
  stopRef.current = stopWhen;

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    let timer: number | undefined;

    const tick = async () => {
      try {
        const result = await fnRef.current();
        if (cancelled) return;
        setData(result);
        setError(null);
        if (stopRef.current(result)) return;
      } catch (err) {
        if (cancelled) return;
        setError(err);
      }
      timer = window.setTimeout(tick, intervalMs);
    };

    void tick();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [enabled, intervalMs]);

  return { data, error };
}
