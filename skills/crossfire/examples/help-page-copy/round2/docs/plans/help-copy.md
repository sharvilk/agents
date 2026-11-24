# Plan: help page for PDF export

PDF export shipped last week (`src/export/formats.js` lists `pdf`), but the help page still only mentions
Markdown.

## Asks

- A1. The "Exporting notes" help section mentions both formats the export menu offers.
- A2. The help banner uses the teal brand colour, as the rest of the help pages already do.

## Change

1. In `src/help/exporting.md`, replace the last sentence with: "You can download it as Markdown or as a PDF."
2. In `config/defaults.json`, change `helpBannerColor` from `"blue"` to `"teal"`.

## Done when

- D1. The help section names Markdown and PDF, matching `EXPORT_FORMATS`.
- D2. The help banner renders teal.

No code changes, no data changes.

## Answers to the review's questions

- Q1. `src/help/banner.js` reads `helpBannerColor` as the default for any help page without its own
  `bannerColor` (`config/help-pages.json`), and maps the name through `src/styles/palette.json`, which has a
  `teal` entry. An unknown name throws when the banner renders.
- Q2. The brand teal is the palette's `teal` entry, `#0f766e` with white text, the same one the account and
  billing help pages use (`config/help-pages.json`). White on `#0f766e` is about 5.5:1, above the 4.5:1 AA bar.
