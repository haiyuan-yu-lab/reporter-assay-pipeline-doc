# CLI overview

Installing the package exposes three commands:

| Command | Role |
| --- | --- |
| [`yulab_reporter_pipe`](pipe.md) | Nine pipeline steps plus grouped orchestration |
| [`yulab_reporter_qc`](qc.md) | Read-only analytical plots over existing artifacts |
| [`yulab_reporter_export`](export.md) | ExogeneousSequences FASTA + stat `.npy` export |

For any installed build, `COMMAND --help` and `COMMAND <subcommand> --help` are
authoritative for flags and defaults. These pages document the **0.1.0b1**
contract.

See also [Workflow](../workflow.md) and [Artifact formats](../formats.md).
