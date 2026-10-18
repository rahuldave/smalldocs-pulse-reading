# Pulse Reading

A SmallDocs reading refinement of [Bootswatch Pulse](https://bootswatch.com/pulse/), based on pinned Bootswatch 5.3.8. It keeps the original light palette and character, with a 640px prose column, calmer heading scale, 1.45 body leading, and locally bundled IBM Plex Mono code at 14.45px on desktop and phones. Controls, links, and status messages receive a contrast pass. Litera also unifies serif paragraph and list typography.

[Theme handbook](https://rahuldave.com/elegant-themes/theme-guide.html#pulse-reading)

## Install

```sh
smalldocs add rahuldave/smalldocs-pulse-reading
```

In `_smalldocs.yml`:

```yaml
theme: pulse-reading
```

This is an independent extension; the bundled `pulse` theme stays unchanged. This extension uses a single native light palette. Folio, Atelier, and Nocturne in the same collection provide paired light/dark alternatives.

[Live demo](https://rahuldave.com/smalldocs-pulse-reading/) · [Original/refined comparison](https://rahuldave.com/elegant-themes/?group=comparisons) · [Source of the original theme](https://bootswatch.com/pulse/)

## Editable source and build

`src/reading.css` is the authored shared reading layer; `src/design.css` contains family-specific choices; `src/theme.json` holds the palette. `vendor/` pins upstream CSS and local fonts, with their licenses. `_extensions/pulse-reading/` is the complete installable result. Builds require no network access after dependency installation.

```sh
uv sync --group dev
uv run python scripts/build_demo.py
uv run pytest -q
uv run smalldocs publish gh-pages example --no-render
```

Source is on `main`; generated example pages are on `gh-pages`. The example content is identical to the comparison gallery. Tests install the extension in a separate consumer and render all four example pages.

The review interprets [Butterick’s Practical Typography](https://practicaltypography.com/) and [Refactoring UI](https://refactoringui.com/). Scores are review judgments, not endorsements by the authors. No book PDFs or extracts are distributed.

## Licenses

Bootswatch/Bootstrap and this reading overlay are MIT licensed. Bundled font licenses are included with each font family. Original Bootswatch copyright and attribution are retained.
