# Task index

Use this index to enter the current-release documentation by the job you need
to do. All pages describe release **0.1.0b2**.

## Learn

- [Assay model](assay-model.md) — understand tested elements, eBC/pBC branches,
  EID/PID identifier domains, PreTran/PostTran libraries, and activity evidence.
- [Canonical glossary](glossary.md) — resolve exact terms such as CW, CCW, UMI,
  Element, ActivityCall, and negative-control list.

## Run

- [Quickstart](quickstart.md) — install the pinned release and check inputs.
- [Prepare inputs](input-preparation.md) — validate FASTQ pairs, references,
  controls, branches, and replicate sets before execution.
- [Layout schemas](layout-schemas.md) — construct and validate Step 2 JSON
  schemas with symbolic examples.
- [Steps 3–5](steps-3-5.md) — match PreTran orientations, merge UMI counts,
  and build crosswalk/cluster references.
- [Steps 6–8](steps-6-8.md) — match post-transfection IDs, quantify molecules,
  and map counts back to elements.
- [Step 9](steps-9.md) — align replicates and produce an activity-by-element
  table for each present branch.
- [Complete command paths](complete-command-paths.md) — follow grouped or
  individual commands across the complete dual-branch example.

## Diagnose

- [FAQ](faq.md) — resolve common setup, retention, pairing, and branch questions.
- [Workflow](workflow.md) — check stage completion criteria, summaries, and
  retained handoffs.
- [Known limitations](known-limitations.md) — review behavior that is incomplete
  or inconsistent in 0.1.0b2.

## Reference

- [Pipeline CLI](cli/pipe.md) — exact pipeline flags and outputs.
- [QC CLI](cli/qc.md) — plot inputs and options.
- [Export CLI](cli/export.md) — ExogeneousSequences export contract.
- [Artifact formats](formats.md) — exact columns and encodings.

## Search suggestions

Native site search is keyword-based. These exact queries are useful entry
points: `eBC` / `pBC` (branches), `EID` / `PID` (identifier domains), `CW` /
`CCW` (orientation), `PreTran` / `PostTran`, `UMI`, `ActivityCall`,
`activity-by-element`, `--min-match-length`, `negative-control-list`,
`zero retained`, `orientation scatter`, and `ExogeneousSequences`.
