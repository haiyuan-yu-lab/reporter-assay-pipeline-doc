# Reporter Assay Pipeline

Command-line toolkit for processing paired-end reporter-assay sequencing data
into element-level activity calls, diagnostic QC plots, and ExogeneousSequences
export artifacts.

| Resource | Link |
| --- | --- |
| Code | [haiyuan-yu-lab/reporter-assay-pipeline](https://github.com/haiyuan-yu-lab/reporter-assay-pipeline) |
| Agent index | [`llms.txt`](llms.txt) |
| Start by task | [Task index](tasks.md) |
| Install | [Quickstart](quickstart.md) |
| Stages | [Workflow](workflow.md) |
| Commands | [CLI overview](cli/index.md) |
| Tables | [Artifact formats](formats.md) |
| Current limitations | [Known limitations](known-limitations.md) |

!!! note "Beta"
    This site documents release **0.1.0b3**. Interfaces may still change before
    a stable release. The public documentation is the released behavioral
    contract; installed `COMMAND --help` describes the command surface of the
    local build. If they disagree, report a defect rather than silently
    assuming one source is correct.

## Choose a path

- **Learn** — [Assay model](assay-model.md) explains what is measured and how
  branches, identifiers, libraries, and orientations relate; the [canonical
  glossary](glossary.md) defines the vocabulary. [Workflow](workflow.md)
  introduces the pipeline stages and
  [artifact formats](formats.md) names the files exchanged between them.
- **Run** — [Quickstart](quickstart.md) covers prerequisites and inputs; the
  [CLI overview](cli/index.md) and [Pipeline CLI](cli/pipe.md) cover commands.
- **Diagnose** — use the [FAQ](faq.md), stage summaries in the [workflow](workflow.md),
  and [known limitations](known-limitations.md).
- **Reference** — consult the [CLI pages](cli/index.md) and [artifact formats](formats.md)
  for exact flags, columns, and encodings.
