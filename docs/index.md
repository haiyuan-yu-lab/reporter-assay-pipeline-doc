# Reporter Assay Pipeline

Command-line toolkit for **reporter-assay** processing (element-level activity,
QC plots, ExogeneousSequences export) and **cap-selection** processing (strand-selected
RNA endpoint bigWig tracks via `cap-assay-pipeline`).

| Resource | Link |
| --- | --- |
| Code (access required) | [DignoMor/reporter-assay-pipeline](https://github.com/DignoMor/reporter-assay-pipeline) |
| Agent index | [`llms.txt`](llms.txt) |
| Start by task | [Task index](tasks.md) |
| Install | [Quickstart](quickstart.md) |
| Stages | [Workflow](workflow.md) |
| Commands | [CLI overview](cli/index.md) |
| Tables | [Artifact formats](formats.md) |
| Current limitations | [Known limitations](known-limitations.md) |

!!! note "Beta"
    This site documents release **0.2.0b2**. Interfaces may still change before
    a stable release. The public documentation is the released behavioral
    contract; installed `COMMAND --help` describes the command surface of the
    local build. If they disagree, report a defect rather than silently
    assuming one source is correct.

## Choose a path

- **Reporter assay** — nine-step QUASARR-seq path to activity-by-element tables.
  Start with [Workflow](workflow.md) and [Pipeline CLI](cli/pipe.md).
- **Cap-selection assay** — four-step fork–join path to signed endpoint bigWigs.
  Start with [Cap-selection workflow](cap-selection/workflow.md) and
  [Cap-selection CLI](cli/cap-assay.md).

- **Learn** — [Assay model](assay-model.md) explains what is measured and how
  branches, identifiers, libraries, and orientations relate (including
  cap-selection endpoints); the [canonical glossary](glossary.md) defines the
  vocabulary. [Workflow](workflow.md) covers reporter-assay stages;
  [artifact formats](formats.md) names files exchanged between stages.
- **Run** — [Quickstart](quickstart.md) covers prerequisites and inputs; the
  [CLI overview](cli/index.md) lists all executables.
- **Diagnose** — use the [FAQ](faq.md), stage summaries in the [workflow](workflow.md),
  and [known limitations](known-limitations.md).
- **Reference** — consult the [CLI pages](cli/index.md) and [artifact formats](formats.md)
  for exact flags, columns, and encodings.
