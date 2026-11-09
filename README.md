# Pulse Reading

A SmallDocs reading refinement of [Bootswatch Pulse](https://bootswatch.com/pulse/), based on pinned Bootswatch 5.3.8. It keeps the original light palette and character, with a 640px maximum prose column, explicit reading hierarchy, 1.6 body leading, and locally bundled IBM Plex Mono code at a 16px reference size. Controls, links, and status messages receive a contrast pass. Litera also unifies serif paragraph and list typography.

[Theme handbook](https://rahuldave.com/elegant-themes/theme-guide.html#pulse-reading)

## Install

```sh
smalldocs add rahuldave/smalldocs-pulse-reading
```

In `_smalldocs.yml`:

```yaml
theme: pulse-reading
```

This is an independent extension; the bundled `pulse` theme stays unchanged. Version 0.2 provides the native light palette and an explicitly designed dark companion. Both are owned Reading adaptations; upstream Bootswatch remains unchanged.

[Live demo](https://rahuldave.com/smalldocs-pulse-reading/) · [Original/refined comparison](https://rahuldave.com/elegant-themes/?group=comparisons) · [Source of the original theme](https://bootswatch.com/pulse/)

## Paired modes and Quarto

SmallDocs exposes its normal light/dark control when this theme is selected. The native light mode retains its paper and brand anchors; the companion is a deliberately authored Reading adaptation. Links, primary fills and their ink have independent roles. Brand colors do not define warning, error or scientific data meanings.

For Quarto 1.8 or later:

```sh
quarto add rahuldave/smalldocs-pulse-reading
```

In `_quarto.yml`:

```yaml
format: pulse-reading-html
```

The extension compiles Quarto's native `pulse` base with an owned light/dark overlay. It never injects the complete SmallDocs Bootstrap bundle into Quarto. Its fonts are a separate CSS dependency so Quarto preserves their resource paths. The mode control follows Quarto's normal behavior.

## Editable source and build

`src/foundations.json` is the authoritative v1 contract for both modes: named swatches, semantic references, interaction/state pairs, font jobs and available weights, reading/presentation profiles, spacing and shape. The installable extension includes an identical `foundations.json` for downstream consumers. `src/theme.json` keeps compatibility metadata; its palette is generated from the native contract mode. Edit foundations rather than generated aliases.

`src/reading.css` maps components to those roles; `src/design.css` is reserved for family-specific rules. Both SmallDocs CSS files and the Bootstrap-free Quarto SCSS overlays are generated. `vendor/` pins upstream CSS and local fonts, with their licenses. Builds require no network after dependency installation. Do not edit vendor CSS to change the Reading adaptation.

Reading body is 18px system sans, UI 16px, metadata 14px, code 16px, title 36px and separate display 48px. These reference values emit rem at a 16px root and honor zoom. Pulse uses platform fonts, so exact metrics vary by operating system. Ordinary prose and headings use primary ink. Panels use radius 4 and no resting shadow. The presentation profile is published for consumers; it does not enlarge the document interface.

Selected controls require a word/checkmark and `aria-selected`, `aria-current` or `aria-pressed`; disabled controls require native `disabled` behavior. Error text needs a named error and `aria-describedby` association. State colors include independent fill, ink and meaningful boundary. Color alone does not supply these semantics.

```sh
uv sync --group dev
uv run python scripts/build_demo.py
uv run pytest -q
uv run smalldocs publish gh-pages example --no-render
```

Tests validate the local schema, opaque contrast pairs, deterministic builds, derived aliases and profile changes. They install freshly generated files through public SmallDocs and Quarto add commands using a temporary committed snapshot, then render `tests/fixtures/components.qmd` in independent consumers. Quarto testing is skipped explicitly if Quarto is unavailable. The fixture covers prose, listing, code, figure, table, callout, links, controls, selected/disabled/error states and all status pairs. Generated acceptance sites remain under ignored `.build/qa/` for browser review. These static and rendering checks do not certify a projector or whole-page accessibility.

Source is on `main`; generated example pages are on `gh-pages`. Website publication is separate from source updates. Existing font-source and license documentation remains applicable.

## Licenses

Bootswatch/Bootstrap and this reading overlay are MIT licensed. Bundled font licenses are included with each font family. Original Bootswatch copyright and attribution are retained.
