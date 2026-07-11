# FAQ

## Where is the source code?

[haiyuan-yu-lab/reporter-assay-pipeline](https://github.com/haiyuan-yu-lab/reporter-assay-pipeline)

## Which version do these docs describe?

**0.1.0b1** (beta). For any installed build, `COMMAND --help` is authoritative.

## Why did my intermediates disappear after a grouped command?

Grouped `yulab_reporter_pipe` commands default to `--delete-intermediate`.
Orchestrator-managed step-to-step files are removed after success; retained
outputs and `*_summary.json` files stay. Pass `--no-delete-intermediate` when
debugging.

## Do I need a special QC install?

No. `pandas` and `matplotlib` are core package dependencies. `pip install .`
provides `yulab_reporter_pipe`, `yulab_reporter_qc`, and `yulab_reporter_export`.

## Is `fastp` pinned?

No. Step 1 / `prep_lib` invoke whichever `fastp` binary is on `PATH`.

## How are forward and reverse references paired?

By **record order**, not by matching `Element` header strings. Both FASTA files
must have the same number of records; record `i` in each file is the same
physical element in opposite orientations. See [Workflow](workflow.md).

## Why do I need two `call_activity` runs?

eBC and pBC are separate branches with different cluster references and
activity tables (typically `EID-ActivityByElement` and `PID-ActivityByElement`).

## How does `process_posttrans` find Step 2 records?

It resolves
`<project-dir>/work/delimited/<library-prefix>_step2_records.tsv.gz`
from `--library-prefix`. Run `prep_lib` for that prefix first (or place an
equivalent file at that path).

## Do QC plots gate the pipeline?

No. QC is inspection-only. It does not apply pass/fail thresholds and does not
modify pipeline artifacts.

## Will there be a documentation chatbot?

Planned. It will answer from this documentation corpus only (with citations).
