# Admin Panel

The `admin-panel` service is the platform’s current operator-facing UI surface. The repository actually contains **two admin-panel implementations/artifact styles** in the same service directory, and understanding that split is important before changing or deploying it.

## 1) What is in `services/admin-panel/`

### Next.js app-router implementation
This is the actively branded operator console defined by:

- `app/layout.js`
- `app/page.js`
- `app/globals.css`
- `components/SectionCard.js`
- `package.json`

This version renders a dark, dashboard-oriented operator console with:
- go-live hero metrics
- affiliate tracking overview
- approval queue
- edge routing map
- production readiness checklist

### Separate Vite-style React SPA artifacts
The same folder also contains a different React SPA-oriented structure:

- `index.html`
- `src/main.jsx`
- `src/App.jsx`
- `src/components/*`
- `src/pages/*`
- `src/styles.css`
- `src/data/mockData.js`

This version models:
- sign-in flow
- role-aware navigation
- overview/user/admin pages
- access-control actions
- rent and billing mock workflows

## 2) Why this matters

The service directory currently mixes two UI directions:

1. **Next.js operational dashboard** — more polished go-live/operator-console narrative.
2. **React SPA workspace** — more workflow-heavy mock application with login and tabbed pages.

Anyone updating the admin panel should decide which runtime is authoritative for the environment they are touching. The repository documents both because both are present in source.

## 3) Runtime and commands

According to `package.json`, the service is currently wired for Next.js:

```bash
npm run dev
npm run build
npm run start
npm run lint
```

This means the app-router implementation is the primary package-managed runtime path today.

## 4) Next.js dashboard information architecture

The current Next.js home page includes four major sections:

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

## 5) React SPA workspace information architecture

The SPA implementation provides:

### Authentication view
- email/password sign-in
- demo credentials for admin and user personas
- invalid-login messaging

### Main navigation
- Overview
- User
- Admin
- Access Control
- Rent Ops

### Example workflow areas
- overview dashboards
- user-specific panels
- admin dashboards
- user status toggles
- billing status updates
- rent-unit status operations

## 6) UX strengths already visible

- clear card-based hierarchy
- compact KPI summaries
- pill-based state indicators
- responsive layout rules in both CSS implementations
- separation between dashboard summary and action-oriented forms
- operator vocabulary that aligns with platform go-live workflows

## 7) Current design risks / cleanup opportunities

- two UI architectures coexist in one service directory, which can confuse onboarding and deployment
- Next.js and SPA implementations are conceptually related but operationally distinct
- mock data and demo auth flows should not be mistaken for production identity or real billing logic
- documentation and deployment should always state which implementation is active in the target environment

## 8) Recommended maintenance rule

Before changing this service, explicitly decide one of the following:

- **Dashboard-first path**: keep Next.js as canonical and archive/segregate the SPA artifacts.
- **Workspace-first path**: convert the SPA features into the Next.js app and retire the duplicate structure.
- **Dual-demo path**: keep both intentionally, but document separate start/build instructions and intended use cases.

## 9) Related documentation

- system overview: `docs/system-overview.md`
- installation: `docs/installation.md`
- admin manual: `docs/manuals/admin-manual.md`
- UX/UI guide: `docs/ux-ui/admin-panel-ux-ui.md`
