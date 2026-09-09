# CLI overview

Installing the package exposes three commands:

| Command | Role |
| --- | --- |
| [`yulab_reporter_pipe`](pipe.md) | Nine pipeline steps, grouped orchestration, and `concat_step2_records` |
| [`yulab_reporter_qc`](qc.md) | Read-only analytical plots over existing artifacts |
| [`yulab_reporter_export`](export.md) | ExogeneousSequences FASTA + stat `.npy` export |

These pages document the released **0.1.0b2** contract for flags and defaults.
`COMMAND --help` and `COMMAND <subcommand> --help` describe the command
surface of the installed local build; if help disagrees with these release
documents, treat the disagreement as a defect.

In **0.1.0b2**, some individual-step help is incomplete. See [Known
limitations](../known-limitations.md). Current local builds print the complete
step-owned command surface from `yulab_reporter_pipe stepN --help`.

See also [Workflow](../workflow.md) and [Artifact formats](../formats.md).
