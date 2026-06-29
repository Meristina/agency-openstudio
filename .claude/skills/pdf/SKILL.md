---
description: Export a mission dossier to a designed PDF — HTML report via Open Design templates + WeasyPrint or browser print
argument-hint: "<mission_id> [--design notion|linear|stripe|minimal]"
---

# /pdf — mission dossier → designed PDF

Converts a mission dossier into a polished PDF using Open Design's bundled
templates when the daemon is running, or generates a rich HTML report directly
using the bundled skill templates (no daemon required).

Open Design app: `/Applications/Open Design.app`
Open Design skills: `/Applications/Open Design.app/Contents/Resources/open-design/skills/`

## Input

`$ARGUMENTS` = mission ID + optional design flag.

```
/pdf 014-je-veux-cr-er-une-app
/pdf 014-je-veux-cr-er-une-app --design linear
/pdf 014-je-veux-cr-er-une-app --design minimal
```

Design options: `notion` (default) · `linear` · `stripe` · `minimal`

---

## Steps

### 1 — Parse & locate

- Parse mission ID and `--design` flag (default: `notion`)
- Find `missions/<mission_id>/deliverable.md` (or `~/.agency/missions/<mission_id>/deliverable.md`)
- If not found → run `agency missions` and stop
- Read the full deliverable content

### 2 — Check Open Design daemon

```bash
curl -sf http://127.0.0.1:7456/api/skills > /dev/null 2>&1 && echo "od:up" || echo "od:down"
```

- **Daemon up → Step 3A** (Open Design path)
- **Daemon down → Step 3B** (direct HTML generation path)

---

### 3A — Open Design daemon path

Call the `data-report` or `pm-spec` skill via REST:

```bash
curl -s -X POST http://127.0.0.1:7456/api/skills/run \
  -H "Content-Type: application/json" \
  -d "{
    \"skill\": \"data-report\",
    \"designSystem\": \"<chosen_design>\",
    \"brief\": \"<brief>\",
    \"outputFormat\": \"html\"
  }" | jq -r '.artifactPath'
```

Then convert HTML → PDF via headless Chrome:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --print-to-pdf="missions/<mission_id>/deliverable-designed.pdf" \
  --no-margins --print-to-pdf-no-header \
  <html_artifact_path>
```

---

### 3B — Direct HTML generation (no daemon needed)

Read the Open Design template approach from:
`/Applications/Open Design.app/Contents/Resources/open-design/skills/data-report/SKILL.md`

Generate a **single-file HTML report** from the deliverable using this layout:

```
┌─────────────────────────────────────────────────────┐
│  HEADER: Mission title · Date · Route · Dept count  │
├─────────────────────────────────────────────────────┤
│  EXECUTIVE SUMMARY (from §I or first 600 chars)     │
├──────────────────┬──────────────────────────────────┤
│  KPI CARDS       │  Market data table               │
│  · Dept count    │  (from §II market context)       │
│  · Source count  │                                  │
│  · Decision count│                                  │
├──────────────────┴──────────────────────────────────┤
│  DECISIONS TABLE (from §VII or decisions section)   │
├─────────────────────────────────────────────────────┤
│  DEPARTMENT SECTIONS (one card per dept in route)   │
├─────────────────────────────────────────────────────┤
│  SOURCES TABLE (from §X or sources section)         │
├─────────────────────────────────────────────────────┤
│  INSPECTOR VERDICT badge (PASS / PASS-WITH-FIXES)   │
│  OPEN ITEMS checklist                               │
└─────────────────────────────────────────────────────┘
```

**Design token sets by flag:**

| Flag | Primary | Accent | Font |
|---|---|---|---|
| `notion` | `#191919` | `#2eaadc` | Inter / system-ui |
| `linear` | `#1a1a2e` | `#5e6ad2` | Geist / system-ui |
| `stripe` | `#0a2540` | `#635bff` | Söhne / system-ui |
| `minimal` | `#000` | `#888` | Georgia / serif |

**HTML requirements (from Open Design `data-report` template):**
- Single inlined HTML file (no external assets except CDN fonts)
- CSS variables for all design tokens
- Responsive layout (max-width: 900px, centered)
- Tables: zebra stripe, hover, sticky header
- Charts (if market data present): Chart.js via CDN — **always wrap `<canvas>` in
  `<div style="position:relative;height:280px">` to prevent ResizeObserver loop**
- KPI cards: value + label, clean grid
- Print-optimised: `@media print { … }` with proper page breaks
- No lorem ipsum, no placeholder data — all content from the actual deliverable

Write the HTML to:
```
missions/<mission_id>/deliverable-designed.html
```

### 4 — Convert HTML → PDF

Try in order:

```bash
# Option A: Chrome headless (best quality)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu \
  --print-to-pdf="missions/<mission_id>/deliverable-designed.pdf" \
  --print-to-pdf-no-header --no-margins \
  "file://$(pwd)/missions/<mission_id>/deliverable-designed.html"

# Option B: WeasyPrint Python (fallback)
agency export <mission_id>
```

### 5 — Open & report

```bash
open "missions/<mission_id>/deliverable-designed.pdf" 2>/dev/null \
  || open "missions/<mission_id>/deliverable-designed.html"
```

Report:
```
✓ PDF exported
  HTML  : missions/<mission_id>/deliverable-designed.html
  PDF   : missions/<mission_id>/deliverable-designed.pdf
  Design: <chosen_design>
```

---

## To enable Open Design daemon (richer output)

```bash
open /Applications/Open\ Design.app   # launch the GUI app
# daemon starts automatically on port 7456
```

The skill auto-detects the daemon and uses it when available.
