# PRD — GlennTek

## Original problem statement
User uploaded an existing full-stack project (Glanetek-main.zip) and asked to "deploy here / build this". Goal: stand up the existing app in this environment and verify it works end-to-end. No feature/design changes requested.

## What the app is
GlennTek — a bilingual (PT default, /en English) Portuguese device-repair business website.
- Public marketing site: hero, device/repair grids, how-it-works, locations, blog, FAQ, reviews.
- Lead/quote request form (public) → stored in MongoDB.
- CMS: services, repairs, brands, districts, municipalities, blog articles, campaigns, FAQs, reviews.
- SEO: sitemap.xml, robots.txt, per-page meta.
- Protected admin panel at /admin: dashboard, leads management, content manager/page editor, SEO & settings.

## Architecture
- Frontend: React 19 (CRA + CRACO), react-router v7, Tailwind, shadcn/ui. Served on :3000. API via `${REACT_APP_BACKEND_URL}/api`, axios withCredentials + X-CSRF-Token.
- Backend: FastAPI on :8001, routers auth/leads/cms/seo, security-headers middleware, CORS locked to FRONTEND_ORIGIN. Managed by supervisor.
- DB: MongoDB (DB_NAME=glanetek_database). Seed runs on startup (devices, repairs, districts, cities, brands, blog, campaigns, settings).
- Auth: HttpOnly cookie session (`gt_session`) + CSRF token header + Origin check + rate limiting. First-time setup gated by ADMIN_SETUP_TOKEN.

## Environment notes (IMPORTANT)
- The ingress proxy REWRITES the incoming `Origin` header to the internal cluster host `…cluster-5.preview.emergentcf.cloud`. Therefore backend/.env `FRONTEND_ORIGIN` is set to that cluster origin so CORS + auth Origin checks pass. Do NOT change it to the public preview URL or auth/CORS will break.
- `SITE_URL` = public preview URL (used for sitemap/canonical).
- Email notifications intentionally DISABLED (settings.email_notifications=false); EMERGENT_EMAIL_KEY configured for later enablement.
- requirements.txt was replaced with the minimal real dependency set (original was a bloated freeze with a litellm/emergentintegrations conflict; backend doesn't use those).

## Implemented / verified (2026-06)
- Full project copied into /app, env configured, deps installed, services running.
- Admin account created: admin@glenntek.com (see /app/memory/test_credentials.md).
- Testing agent: backend 100% (12/12 pytest), frontend 100% — homepage renders (PT + /en), all key pages 200, lead submission → 201 with confirmation, admin login + dashboard + leads list, SEO endpoints, health.
- Fixed: Footer missing React `key` warning; invalid HTML5 phone `pattern` regex in QuoteForm.

## Backlog (not requested; optional)
- P2: Configure real business settings (name, phone/WhatsApp, address, analytics IDs) via admin Settings.
- P2: Enable lead email notifications (set admin_email + toggle) if desired.
- P2: Populate real reviews and blog content via CMS.

## Next tasks
- None outstanding. App is deployed and functional.
