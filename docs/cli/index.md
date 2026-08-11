# CLI overview

Installing the package exposes three commands:

| Command | Role |
| --- | --- |
| [`yulab_reporter_pipe`](pipe.md) | Nine pipeline steps plus grouped orchestration |
| [`yulab_reporter_qc`](qc.md) | Read-only analytical plots over existing artifacts |
| [`yulab_reporter_export`](export.md) | ExogeneousSequences FASTA + stat `.npy` export |

These pages document the released **0.1.0b2** contract for flags and defaults.
`COMMAND --help` and `COMMAND <subcommand> --help` describe the command
surface of the installed local build; if help disagrees with these release
documents, treat the disagreement as a defect.

Some individual-step help is incomplete in this release. See [Known
limitations](../known-limitations.md) before relying on installed help.

See also [Workflow](../workflow.md) and [Artifact formats](../formats.md).
