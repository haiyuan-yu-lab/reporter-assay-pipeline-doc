# CLI overview

Installing the package exposes four commands:

| Command | Role |
| --- | --- |
| [`yulab_reporter_pipe`](pipe.md) | Nine reporter-assay steps, grouped orchestration, and `concat_step2_records` |
| [`yulab_reporter_qc`](qc.md) | Read-only analytical plots over existing reporter-assay artifacts |
| [`yulab_reporter_export`](export.md) | ExogeneousSequences FASTA + stat `.npy` export |
| [`cap-assay-pipeline`](cap-assay.md) | Four cap-selection steps to strand-separated RNA endpoint bigWigs |

These pages document the released **0.1.0b3** contract for flags and defaults.
`COMMAND --help` and `COMMAND <subcommand> --help` describe the command
surface of the installed local build; if help disagrees with these release
documents, treat the disagreement as a defect.

In **0.1.0b3**, each `yulab_reporter_pipe stepN --help` request prints the
complete step-owned command surface.

See also [Workflow](../workflow.md) and [Artifact formats](../formats.md).
