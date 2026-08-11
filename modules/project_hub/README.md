# Project Hub — TRIZ Platform module

Drops into `TRIZ Platform/modules/`. The registry discovers it via
`manifest.json`; no changes to `triz_platform.py` are required.

## Install

Copy this whole `project_hub/` folder into `E:\TRIZ Platform\modules\`, then:

    pip install PyMuPDF openpyxl ezdxf

Launch the platform — "Project Hub" appears under **Drawing Automation**.

## How it docks

`page.py` wraps `HubShell`, the same widget the standalone Hub window hosts, so
there is one engine implementation rather than a fork. The adapter handles only
the integration seams:

| Seam | Standalone | Docked |
|---|---|---|
| Settings | `QSettings` | `ModuleSettings` -> `settings/project_hub.json` |
| Status text | own status bar | inline strip + `platform.output_write()` |
| Index finished | log only | `platform.notify()` |
| Search focus | Ctrl+K / Ctrl+F | Ctrl+F only (Ctrl+K stays with the palette) |
| Stylesheet | app-level | scoped to the page subtree |

That last row matters: the Hub's "Drafting" design system and the platform
`STYLE` both style `#Card`, `#Sidebar`, and `#Title`. A widget-level stylesheet
wins over the application one for that subtree, so the Hub keeps its own look
without touching how any other module renders.

## Engine

`triz_hub/core/` has no Qt imports — indexer, tag patterns, issue rules, and
extractors are reusable from other modules. The `documents` table is the
intended data source for Deliverable Publisher (latest-rev lists) and Title
Block Manager (read side).
