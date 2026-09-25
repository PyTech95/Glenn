# Glanetek — Deploy Your Project Here

Bring your uploaded Glanetek project into this workspace, get it running live in preview, and make it ready for one-click deployment.
The uploaded code is adapted so it runs reliably on this platform, keeping the look and behavior of your original as intact as possible.

## Who it's for
You — the owner of the Glanetek project — who wants the existing code taken from a zip and turned into a working, deployable site/app running on this platform.

## Core features and experience
- Your Glanetek project is unpacked and brought into the workspace.
- The site/app loads in the live preview with its existing pages, layout, and styling intact.
- Any interactive parts (navigation, forms, buttons, content sections) work as they did in the original.
- Broken links, missing images, or parts that don't survive the move are fixed so the app is presentable end to end.
- Once it runs cleanly in preview, it is ready for the platform's Deploy button to go live on a public URL.

## User flow
1. A visitor opens the deployed URL.
2. They land on the Glanetek home page and can move through its pages/sections.
3. They interact with whatever the original supports (menus, forms, calls-to-action) and get the expected response.
4. Anything that talks to a backend or external service responds correctly once configured.

## UI/UX feel
Preserve the original Glanetek design — its colors, fonts, spacing, and page structure. The goal is fidelity to what you built, not a redesign. Where something is missing or broken after the move, it's repaired to match the surrounding style rather than restyled.

## Implementation phases

### Phase 1 — MVP (built now)
- Unpack the uploaded project and review its structure and stack.
- Get the frontend building and rendering in the live preview with original pages and styling.
- Stand up whatever backend/data the project needs so its core screens and interactions work.
- Fix load-blocking issues (build errors, broken asset paths, obviously broken links).
- Deliver an app that runs cleanly in preview and is ready for the Deploy button.

### Phase 2 — Integrations & data
- Wire up any external services the project expects (e.g. payments, email, maps, sign-in, analytics) using keys you provide.
- Connect persistent data (forms saving, content storage, user accounts) if the project calls for it.
- Verify each connected feature works end to end.

### Phase 3 — Polish & go-live hardening
- Responsive/mobile pass and cross-page consistency cleanup.
- SEO basics (title, description, favicon, social preview) and performance tidy-up.
- Final deploy to a public URL and a smoke test of every page and flow.

## Assumptions
- **Best-judgment mode**: you skipped clarification, so the choices below are mine and can be corrected on review.
- **What Glanetek is**: assumed to be a web frontend project (the zip name matches a GitHub archive download). Treated as a company/agency-style site with multiple pages unless the code shows otherwise.
- **Stack fit**: this workspace runs React + FastAPI + MongoDB. The uploaded code will be adapted to run on this stack rather than reproducing its original server setup exactly. If the original is already React-based, its components/pages are reused directly.
- **Backend/data**: assumed minimal or none for the MVP. If the project needs saved data or accounts, that lands in Phase 2 unless it's required just to render the pages.
- **Integrations/keys**: none set up in Phase 1. Any third-party service (payments, email, login, maps, LLM, etc.) is deferred to Phase 2 and needs credentials from you.
- **Deploy as-is**: the uploaded code is treated as the intended final version; only fixes needed to make it run and look right are applied, no feature changes.
- **Content**: existing text and images from the zip are kept as-is; missing images are replaced with fitting stand-ins.
- **"Deploy here"**: interpreted as making the project run in this platform's preview and ready for its Deploy button; the actual go-live click is the final step.
