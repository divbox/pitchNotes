# Design preferences

Design system for Pitch Notes. This copy has been customized for this project — it's no longer the generic personal template, it's Pitch Notes as it needs to be.

## Philosophy

- CSS custom properties (root variables) for everything — no hardcoded colors scattered through stylesheets
- Self-contained HTML artifacts: portable, shareable, no external dependencies unless CORS is confirmed
- Dark-only. Stadium-navy background, no light mode toggle — this is a fixed design decision, not a default awaiting an override.
- No real team crests or logos anywhere — they're trademarked. Use flat color chips (each club's actual kit color) with 2–3 letter initials instead.
- Status colors (green/orange/red) are semantic and fixed. Don't reassign them.

## Fonts

Three fonts, each with a job: display numerals, editorial body copy, data/labels. Google Fonts is allowed in this project.

```css
@import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap');
```

```css
:root {
  --font-display: 'Big Shoulders Display', system-ui, sans-serif; /* headlines, scoreboard numerals */
  --font-serif:   'Source Serif 4', Georgia, serif;                /* body / editorial copy */
  --font-mono:    'IBM Plex Mono', 'Courier New', monospace;       /* data, labels, tags */
}
```

## Color palette — Stadium Navy

Arsenal red accent, gold trim, warm off-white ink on a dark navy ground.

```css
:root {
  /* Accent */
  --color-accent:        #ef0107;   /* Arsenal red — section tags, primary accent */
  --color-accent-bg:     #2a0a08;
  --color-accent-text:   #ff4d43;
  --color-gold:          #d4a94e;   /* trim / highlights only, not a second accent */

  /* Surfaces */
  --surface-page:        #060d18;
  --surface-card:        #0a1628;
  --surface-subtle:      #101f36;

  /* Text */
  --text-primary:        #f1ede2;
  --text-secondary:      #b8b2a3;
  --text-muted:          #7a7568;

  /* Borders */
  --border:              #1c2d47;
  --border-strong:       #2a3f5c;

  /* Status — semantic, adjusted for dark ground */
  --color-success:       #16a34a;
  --color-success-bg:    #0d2618;
  --color-success-text:  #4ade80;

  --color-warning:       #ea580c;   /* orange, not yellow — distinct from yellow on dashboards */
  --color-warning-bg:    #2b1608;
  --color-warning-text:  #fb923c;

  --color-danger:        #dc2626;
  --color-danger-bg:     #2a0d0d;
  --color-danger-text:   #f87171;

  /* Typography scale */
  --text-xs:   11px;
  --text-sm:   13px;
  --text-base: 16px;
  --text-lg:   18px;
  --text-xl:   22px;

  /* Spacing */
  --radius:    8px;
  --radius-lg: 12px;
}
```

## Dashboard conventions

For stat cards and metric displays:

```css
.stat-card {
  background: var(--surface-card);
  border: 0.5px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem 1rem;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 500;
  margin-bottom: 4px;
}

.stat-value {
  font-size: var(--text-lg);
  font-weight: 500;
  color: var(--text-primary);
}
```

Status cells use the semantic color pair: `--color-{status}-bg` for background, `--color-{status}-text` for text and label. Never mix status colors across palettes.

## HTML artifacts

- Self-contained single files — all CSS and JS inline, no separate files
- Data processing: if heavy lifting is needed, do it in Python first and bake the result into the HTML. This removes the JS processing layer from the artifact and keeps the page lean.
- API data: fetch directly from the page if CORS allows. If not, pre-process and embed.
- Multi-tab layouts are fine when content genuinely separates into distinct views.
- No external CDN dependencies unless you've confirmed they'll be available in the target environment.
