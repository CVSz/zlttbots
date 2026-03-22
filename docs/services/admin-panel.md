# Admin Panel

The `admin-panel` service is the platform’s current operator-facing UI surface. The unused legacy SPA files were removed, so the service now has a single authoritative implementation: the Next.js app-router dashboard in `services/admin-panel/`.

## 1) Active service structure

The active operator console is defined by:

- `app/layout.js`
- `app/page.js`
- `app/globals.css`
- `components/SectionCard.js`
- `package.json`
- `docker/Dockerfile`

This implementation renders a dark, dashboard-oriented operator console with:

- go-live hero metrics
- affiliate tracking overview
- approval queue
- edge routing map
- production readiness checklist

## 2) Runtime and commands

According to `package.json`, the service is wired for Next.js:

```bash
npm run dev
npm run build
npm run start
npm run lint
```

The Docker image also builds and serves the same Next.js application, so there is no longer a separate SPA runtime path to maintain in this directory.

## 3) Dashboard information architecture

The current home page includes four major sections:

### Hero / executive summary
Displays:

- tracked revenue
- edge health
- open reviews
- short positioning statement for unified operations

### Affiliate tracking overview
Shows:

- tracked clicks
- conversions
- conversion rate
- net revenue
- partner table with status pills

### Approval queue
Shows:

- campaign controls
- daily approval cap
- region selector
- review lane selector
- current queue items with workflow state

### Edge routing map and readiness checklist
Shows:

- recommended host-to-service boundaries
- access-control guidance for critical surfaces
- go-live readiness items

## 4) Current maintenance rule

When updating this service, treat the Next.js app-router implementation as the canonical admin experience. New operator workflows should be added into the existing app structure instead of introducing a second frontend runtime in the same directory.

## 5) Related documentation

- system overview: `docs/system-overview.md`
- installation: `docs/installation.md`
- admin manual: `docs/manuals/admin-manual.md`
- UX/UI guide: `docs/ux-ui/admin-panel-ux-ui.md`
