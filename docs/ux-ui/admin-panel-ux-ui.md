# Admin Panel UX/UI Guide

This document is the full-detail UX/UI reference for the `admin-panel` area of zlttbots.

## 1) Scope

The repository currently contains two related UI expressions inside `services/admin-panel/`:

1. a **Next.js operator console** optimized for executive/ops visibility
2. a **React SPA workspace** optimized for sign-in, role navigation, and mock operational actions

This guide covers both so designers, frontend engineers, and platform owners can reason about the current UX state.

## 2) Primary UX goals

The admin UI is trying to support five user needs:

- understand platform health quickly
- inspect business KPIs without querying raw APIs
- move between overview and action-oriented workflows fast
- distinguish safe/healthy vs warning states visually
- keep operator cognition focused with dashboard cards rather than dense raw tables alone

## 3) Next.js operator console UX

### Layout structure
- top hero section with badge, title, narrative, and three summary stats
- stacked card grid for operational domains
- strong dark-theme contrast for control-room feel
- responsive collapse for tablet/mobile breakpoints

### Visual language
- dark radial background
- high-contrast text on panel cards
- accent blue for navigation/importance
- green, amber, and blue status pills for state communication
- rounded cards and moderate spacing for scannability

### Information hierarchy
1. top-level platform health and revenue summary
2. KPI detail block
3. queue and approval workflow
4. edge routing boundaries
5. go-live checklist

### Interaction model
This view is mostly read-oriented today, with light form affordances in the approval queue card. It feels like a readiness and monitoring console rather than a transaction-heavy admin surface.

## 4) React SPA workspace UX

### Entry experience
- centered login card
- short product framing copy
- explicit sign-in action
- inline error handling for invalid credentials

### Navigation model
- horizontal tabbed navigation
- role display in the header
- persistent logout affordance
- pages grouped by task domain instead of deep menu nesting

### Workflow style
The SPA is more action-oriented than the Next.js dashboard. It includes:
- mutable user state
- billing status updates
- settings toggles
- rent operations

This makes it useful for prototyping operator workflows, but it should be clearly labeled as mock/demo behavior until backed by real APIs.

## 5) Responsive behavior

### Next.js dashboard CSS behavior
The layout adapts at narrower widths by:
- stacking the hero vertically
- collapsing multi-column KPI/form grids from 4/2 columns to 1–2 columns
- turning toolbar-like rows into vertical flows on small screens

### SPA CSS behavior
The SPA uses fluid grids (`auto-fit`, minmax-based layouts) and panel cards, which supports dashboard resizing without requiring deep breakpoint-specific redesign.

## 6) Accessibility and usability observations

### Positive traits
- visible text labels for inputs
- clear section headers
- semantic tables for structured data
- color use supported by text labels such as `Healthy`, `Review`, `Approved`, `paid`, `overdue`
- simple navigation depth

### Improvement opportunities
- add explicit focus styles for keyboard users
- ensure color contrast remains valid across all pill states
- add aria/current-page semantics if navigation expands
- unify input spacing and control density across both implementations
- ensure demo credentials are never exposed in production-facing documentation/UI

## 7) Recommended UX direction

### Recommended canonical direction
Use the **Next.js app-router implementation as the canonical shell** and gradually fold the richer SPA workflow modules into it. This aligns runtime tooling with `package.json` and avoids long-term duplicate UI maintenance.

### Suggested migration sequence
1. keep the current Next.js dashboard as the main entry surface
2. port the SPA login, role navigation, and action pages into the Next.js app structure
3. replace mock data with API-backed calls in phases
4. remove or archive duplicate SPA-only artifacts once feature parity is reached

## 8) UX checklist for future changes

Before merging admin-panel UI work, confirm:
- which implementation was changed
- whether the target flow is read-only or action-heavy
- whether labels, pills, and states remain consistent
- whether mobile/tablet layouts were considered
- whether the documentation reflects the chosen canonical runtime
- whether any demo/mock behavior could be mistaken for production logic
