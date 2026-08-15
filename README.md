# SunBridge Trading -- Task 1: China -> Nepal

AI-assisted extraction and reconciliation pipeline for two conflicting
Deye manufacturer datasheets (the AM2-P1 and AM2 variants), producing
a compliance-review draft for SunBridge's import agent, focused on the
5 kW model (`SUN-5K-G06P3`).

## What this does

```
Source PDFs (2)
    |
    v
download           -- fetch the two datasheets from deyeinverter.com
    |
    v
extract             -- pdfplumber: pull every word + its (x, y) position
    |
    v
parse layout         -- reconstruct the visual table: find the model-header
    |                    row, cluster remaining words into rows by y, assign
    |                    each value to the nearest model column by x
    v
build table           -- clean labels/values into {parameter, values{model:val}}
    |                    rows, with confidence + flags per row
    v
normalize             -- reshape into a clean {parameters, by_model} schema,
    |                    fix encoding artifacts, expand shared/multi-model rows
    v
validate               -- sanity-check the normalized data, surface warnings
    |
    v
reconcile (Gemini)      -- compare Source 1 vs Source 2 for SUN-5K-G06P3 only:
    |                       agree / conflict / only-in-one-source / not-established
    v
generate report (Gemini) -- turn the reconciliation into the Markdown draft
                            SunBridge would actually hand to its agent
```

## How to run it

```bash
uv sync
cp .env.example .env   # add your GEMINI_API_KEY
uv run python main.py
```

That single command runs the entire pipeline end to end for both
sources. Every step is idempotent -- if a file for a given step
already exists (e.g. `data/raw/source_1.pdf`), that step is skipped,
so re-running after a crash (most likely: a missing `GEMINI_API_KEY`)
doesn't re-download or re-parse anything.

Outputs land in `data/output/`:

- `reconciliation.json` -- the structured, field-by-field comparison
  (machine-readable, with per-field source attribution)
- `compliance_draft.md` -- the human-readable draft for the agent

To re-run a single stage in isolation (useful while debugging one
source):

```bash
uv run python table_parser.py                 # both sources
uv run python normalize_parser.py source_1    # one source
uv run python validator.py source_2           # one source
```

## Why deterministic extraction + an LLM reconciliation step, not an LLM doing the extraction itself

The two hardest problems here are different in kind:

- **Getting numbers out of the PDF table** is a *geometry* problem --
  which value sits under which model-header column. A coordinate-based
  parser (pdfplumber word positions -> nearest-column assignment) is
  more auditable and repeatable for this than asking a model to read a
  table image or dumped text and hope it keeps 8 columns straight. Every
  row carries a `confidence` and `flags` field so a low-confidence
  extraction is visible rather than silently trusted.
- **Deciding what a mismatch between two documents means for an import
  review** is a *judgment* problem -- this is where Gemini is used,
  constrained to the two already-normalized JSON documents (no web
  search, no outside knowledge, no inventing or copying values between
  models -- see `workflow/prompt.py`), to reconcile per-field agreement/
  conflict/source-only status for `SUN-5K-G06P3` specifically, then to
  write the prose draft from that structured reconciliation, not from
  the raw documents.

### Known limitation of this design

The geometric extraction path is tuned to this specific document
family: the Deye datasheets used here list 8 power-rating variants as
column headers (`SUN-4K` ... `SUN-15K`), and `layout_parser.py` finds
the spec-table page by looking for the page with the most `SUN-`
prefixed words. If a revision changed the number of model columns,
this degrades to a printed warning rather than a hard crash (see
`EXPECTED_MODEL_COLUMNS` in `layout_parser.py`), but the row-clustering
and column-assignment heuristics (`ROW_TOL`, `LABEL_MAX_X`) are still
tuned to this layout family and haven't been tested against a visually
different datasheet. With more time, the right fix is a verification
pass: after the deterministic parse, ask Gemini to spot-check the
extracted table against the raw page text/image and flag likely
misalignments, rather than trusting the geometry alone.

## Assumptions

- SunBridge is ordering the 5 kW model (`SUN-5K-G06P3`), per the brief
  -- the reconciliation step is scoped to that model only, even though
  both datasheets list all 8 variants.
- A value is only attributed to `SUN-5K-G06P3` if it's explicitly
  under that column; a value that's true for another model in the same
  table is never assumed to also apply to the 5 kW model.
- "Agrees" means the same value under reasonable unit/wording
  normalization (e.g. `98.1%` vs `98.1 %`), not exact string equality.
- Where the two sources use different labels for what looks like the
  same underlying spec, that's surfaced as a possible match for a human
  to confirm, not silently merged.

## Known issues fixed while reviewing this repo

While wiring the pipeline together end-to-end for this submission, a
few pre-existing bugs surfaced and were fixed:

- **`normalize_parser.py` was silently dropping shared-value rows.**
  `table_parser.py` supports an `"ALL_MODELS"` key (e.g. `IP65` stated
  once for the whole product family) and comma-joined multi-model keys.
  `normalize_row()` only ever matched exact single model names against
  those keys, so any row using either convention ended up `null` for
  every model even though the source document had a real, common
  value. Fixed to expand both cases to their individual model keys.
- **`validator.py` was validating the wrong schema.** It read
  `data/normalized/*.json` (which `normalize_parser.py` shapes as
  `{"parameters": ..., "by_model": ...}`) but checked for a `"rows"`
  key that only exists in `data/tables/*.json` (`table_parser.py`'s
  output, one stage earlier). It always reported `"No rows found."`
  and never actually validated anything. Rewritten to check the real
  `parameters`/`by_model` shape.
- **The pipeline wasn't wired together.** `main.py` only invoked the
  LangGraph reconciliation step and required `data/normalized/*.json`
  to already exist, with no code path that produced those files. Every
  earlier stage (download, extract, layout-parse, table-parse,
  normalize, validate) had to be run by hand, in the right order, once
  per source -- and two of those stages (`downloader.py`,
  `pdf_extractor.py`) had no CLI entry point at all. `main.py` now
  calls every stage in sequence.
- Removed two empty/orphaned files (`report_generator.py`,
  `src/ai_assessment/pdf_inspector.py`) that were never imported
  anywhere, and removed the leftover `uv init` console-script stub in
  `pyproject.toml` that printed `"Hello from ai-assessment!"` instead
  of running anything real.

## What I'd do with more time

- Add the Gemini-based table-extraction verification pass described
  above, instead of relying solely on geometric heuristics.
- Test the layout parser against a third-party datasheet with a
  different column count to actually exercise the fallback path in
  `get_relevant_page()`.
- Add automated tests around `normalize_parser.py`'s `ALL_MODELS`/
  comma-key expansion and `table_parser.py`'s noise-row detection --
  both were only caught by manual inspection here.
- Surface `validate_source()`'s warnings inside the generated Markdown
  report itself (e.g. an "extraction confidence" appendix), not just
  in the console log, so the agent-facing document is explicit about
  where the pipeline was unsure.

## Repo layout

```
main.py                    # pipeline entry point (uv run python main.py)
table_parser.py            # data/parsed -> data/tables
normalize_parser.py        # data/tables -> data/normalized
validator.py                # sanity-checks data/normalized
src/ai_assessment/
  config.py                 # source URLs, target model, data dir layout
  downloader.py              # PDF download
  pdf_extractor.py           # pdfplumber word/coordinate extraction
  layout_parser.py           # visual table reconstruction
workflow/
  state.py                   # LangGraph shared state
  nodes.py                   # load_normalized_data / reconcile / generate_report
  prompt.py                  # reconciliation + report-generation prompts
  graph.py                   # LangGraph wiring
```
