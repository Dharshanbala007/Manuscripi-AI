// Local (default) vs hosted demo. Hosted builds set VITE_HOSTED=true at build time.
// The two differ in what we can honestly promise: locally nothing leaves the machine; hosted, the
// file is uploaded to the server (and removed automatically), so the copy must say so.

export const HOSTED = import.meta.env.VITE_HOSTED === "true";

const LOCAL = {
  privacyBadge: "Processed locally — your manuscript never leaves this machine",
  tag: "Rule-based · offline-capable",
  heroTail: " — all on this machine.",
  privateStep: "Private — processing runs locally; nothing is uploaded to any external service.",
  historyNote: "Local history — stored on this machine, no manuscript content.",
  analyzing: "This runs locally on your machine.",
  exports: "Verified files, generated locally.",
  footer: "ManuScript AI · rule-based, offline-capable · IEEE and Springer format profiles",
};

const HOSTED_COPY: typeof LOCAL = {
  privacyBadge: "Hosted demo — your file is uploaded to the server and removed automatically",
  tag: "Rule-based · deterministic",
  heroTail: ".",
  privateStep:
    "Temporary — your file is uploaded to this demo's server and deleted automatically; only its name, scores and counts are kept in history.",
  historyNote: "History for this browser — file names and scores only, no manuscript content.",
  analyzing: "This runs on the server.",
  exports: "Verified files, generated on the server.",
  footer: "ManuScript AI · rule-based · IEEE and Springer format profiles",
};

export const COPY = HOSTED ? HOSTED_COPY : LOCAL;

// An anonymous per-browser id. The shared server scopes history by it, so visitors never see each
// other's file names. Not a login and not a secret; it just keeps histories apart.
const KEY = "manuscript-client-id";
let fallback: string | undefined;

export function clientId(): string {
  try {
    let id = localStorage.getItem(KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    // Storage blocked: keep one id for this page load so history still works until the tab closes.
    return (fallback ??= crypto.randomUUID());
  }
}
