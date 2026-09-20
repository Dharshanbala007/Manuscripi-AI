# ManuScript AI — 21st.dev Restyle & Morphing Flow

**Date:** 2026-09-20
**Status:** Approved (chat). Decisions: full morphing flow, light refined-glass look.
**Builds on:** Slices 1–3 (all merged). Visual/interaction change only — no backend,
route, or copy changes beyond what the restyle needs.

## 1. Constraint discovered during build

The 21st free tier allows **2 component-code retrievals per day** and AI generation is
disabled. Two components were retrieved and adapted; everything else follows the same
visual language but is written in-repo:

| Source | Component | Used for |
|---|---|---|
| 21st.dev `@ddoemonn/loading-button` (id 23536) | label morphs idle → pending → success → error, no layout shift | `MorphButton` — every async action |
| 21st.dev `@ibelick/morphing-dialog` (id 1438) | trigger expands into the dialog via shared `layoutId` | Apply-format dialog |
| In-repo (motion `layoutId`) | glass surfaces, morphing flow rail, animated tabs, dropzone | everything else |

Adapting the retrieved code required fixing defects in the originals: a missing
`use-click-outside` hook, `aria-labelledby`/`aria-describedby` ids that nothing defined,
a non-focusable trigger whose focus-restore ref was never attached, and a Tab trap that
cached focusables once at open (breaks when content loads late).

## 2. Design

- **Foundation:** `@/` alias (vite, vitest, tsconfig), `components.json`, `cn` =
  clsx + tailwind-merge v2 (v3 is Tailwind-4-only), `tailwindcss-animate`, `motion`.
  shadcn-style HSL tokens; brand indigo becomes `primary`, `accent` becomes the soft tint.
- **Look:** light refined glass — translucent white cards with blur and hairline rings,
  soft aurora gradient mesh behind the page, larger radii, indigo brand kept. WCAG AA
  contrast must still pass the axe suite.
- **Morphing flow:** a persistent glass surface with a shared `layoutId` morphs
  dropzone → file card → analysis card → workspace header. A flow rail
  (Upload · Analyze · Review · Format · Export) has an indicator that slides between
  steps. Status pills, tabs indicator, and buttons morph. Routes and URLs unchanged.
- **Accessibility:** `MotionConfig reducedMotion="user"`, no nested interactives,
  dialog keeps role/name/focus trap, accessible names unchanged.

## 3. Tasks

1. Foundation (aliases, tokens, cn, motion config, background mesh).
2. Token rename + `Button` / `Card` / `Badge` / `Tabs` / `Toast` / `Field` restyle.
3. Adapted 21st components: `use-click-outside`, `MorphingDialog`, `MorphButton`;
   `FormatPicker` on the dialog, TopBar button as morph origin.
4. Morphing flow: flow rail, stage surface, route transitions, dropzone, tab indicator,
   status-pill morph.
5. Tests: update unit/e2e for new markup; add morph e2e + component tests.
6. Browser walkthrough with screenshots, fix findings, docs/credits, full regression.

## 4. Acceptance

`bash scripts/check.sh` green (ruff, pytest, tsc, vitest, Playwright incl. axe), the flow
visibly morphs through every stage in a real browser, and reduced-motion disables motion.
