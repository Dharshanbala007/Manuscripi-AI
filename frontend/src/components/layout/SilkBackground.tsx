import { useEffect, useRef } from "react";

// Adapted from a user-supplied "silk" canvas component. Changes: rendered at a quarter of
// at most a quarter of the viewport and never wider than ~320px (the silk is smooth, so CSS
// upscaling is invisible while cost stays flat on large screens); noise precomputed once per resize; time
// driven by elapsed ms (so speed is constant at any update rate) and adaptive: the frosted
// glass on top re-blurs whenever the canvas changes, so if the page's own frame rate sags the
// canvas updates less often, down to a slow drift, rather than making the UI stutter; a single static frame under
// prefers-reduced-motion; darker violet tint so text on the glass keeps AA contrast; the
// vignette moved to CSS instead of a per-frame canvas gradient.
const MAX_SCALE = 0.25;
const TARGET_WIDTH = 320;
const BASE_FRAME_MS = 1000 / 20;
const FLOOR_FRAME_MS = 1000 / 8;
const SPEED = 0.02;
const TEX_SCALE = 2;
const NOISE = 0.8;
const TINT = [104, 92, 168] as const;
const GAIN = 0.5;

function noise(x: number, y: number): number {
  const G = 2.71828;
  return (G * Math.sin(G * x) * G * Math.sin(G * y) * (1 + x)) % 1;
}

export function SilkBackground() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0;
    let h = 0;
    let image: ImageData;
    let grain: Float32Array;
    let t = reduced ? 40 : 0;
    let last = 0;
    let lastRaf = 0;
    let strain = 0;
    let frameMs = BASE_FRAME_MS;
    let raf = 0;

    const draw = () => {
      const data = image.data;
      const off = SPEED * t;
      for (let y = 0; y < h; y++) {
        const v = (y / h) * TEX_SCALE;
        for (let x = 0; x < w; x++) {
          const u = (x / w) * TEX_SCALE;
          const ty = v + 0.03 * Math.sin(8 * u - off);
          const p =
            0.6 +
            0.4 *
              Math.sin(
                5 * (u + ty + Math.cos(3 * u + 5 * ty) + 0.02 * off) +
                  Math.sin(20 * (u + ty - 0.1 * off)),
              );
          const k = Math.max(0, p - grain[y * w + x]) * GAIN;
          const i = (y * w + x) * 4;
          data[i] = TINT[0] * k;
          data[i + 1] = TINT[1] * k;
          data[i + 2] = TINT[2] * k;
          data[i + 3] = 255;
        }
      }
      ctx.putImageData(image, 0, 0);
    };

    const resize = () => {
      const scale = Math.min(MAX_SCALE, TARGET_WIDTH / window.innerWidth);
      w = Math.max(1, Math.ceil(window.innerWidth * scale));
      h = Math.max(1, Math.ceil(window.innerHeight * scale));
      canvas.width = w;
      canvas.height = h;
      image = ctx.createImageData(w, h);
      grain = new Float32Array(w * h);
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) grain[y * w + x] = (noise(x, y) / 15) * NOISE;
      }
      draw();
    };

    const tick = (now: number) => {
      raf = requestAnimationFrame(tick);

      // Page-wide frame gap: ~16ms is healthy; sustained >30ms means the compositor is struggling.
      const gap = now - lastRaf;
      lastRaf = now;
      if (gap > 250) strain = 0; // tab was hidden, not slow
      else if (gap > 30) strain++;
      else strain = Math.max(0, strain - 1);
      if (strain >= 20 && frameMs < FLOOR_FRAME_MS) {
        frameMs = Math.min(FLOOR_FRAME_MS, frameMs * 1.5);
        strain = 0;
      }

      const dt = now - last;
      if (dt < frameMs) return;
      t += Math.min(dt, 150) / (1000 / 60);
      last = now;
      draw();
    };

    resize();
    window.addEventListener("resize", resize);
    if (!reduced) raf = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div aria-hidden="true" data-testid="silk-background" className="pointer-events-none fixed inset-0 -z-10">
      <canvas ref={ref} className="h-full w-full" />
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at 50% 40%, transparent 0%, rgba(4,4,10,0.35) 60%, rgba(4,4,10,0.75) 100%)," +
            "linear-gradient(to bottom, rgba(0,0,0,0.25), transparent 35%, rgba(0,0,0,0.45))",
        }}
      />
    </div>
  );
}
