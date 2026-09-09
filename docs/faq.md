# FAQ

## Where is the source code?

[haiyuan-yu-lab/reporter-assay-pipeline](https://github.com/haiyuan-yu-lab/reporter-assay-pipeline)

## Which version do these docs describe?

**0.1.0b3** (beta). The public documentation describes the released
behavioral contract. `COMMAND --help` describes the command surface of the
installed local build; disagreements are defects.

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
physical element in opposite orientations. This applies to dual-orientation
`process_pretrans` and `plot_orientation_scatter`. ExogeneousSequences export
uses repeatable `--reference` in CLI order and does not require equal counts.
See [Workflow](workflow.md).

## Can I run CW-only / EID-only PreTran?

Yes. Use `process_pretrans_cw_only` with `--id-columns EID` (and a single
`--forward-reference`). Step 5 emits only the EID cluster reference. Skip the
pBC branch for post-transfection / activity / export. See
[Pipeline CLI](cli/pipe.md).

## Why do I need two `call_activity` runs?

eBC and pBC are separate branches with different cluster references and
activity tables (typically `EID-ActivityByElement` and `PID-ActivityByElement`).
EID-only libraries only need the eBC run.

## How does `process_posttrans` find Step 2 records?

It resolves
`<project-dir>/work/delimited/<library-prefix>_step2_records.tsv.gz`
from `--library-prefix`. Run `prep_lib` for that prefix first (or place an
equivalent file at that path). If the replicate was parsed twice with
orientation-specific layouts, concatenate those gzip-compressed tables into
that path with [`concat_step2_records`](cli/pipe.md#concat_step2_records)
first.

## How do I concatenate orientation-specific Step 2 tables?

Use `yulab_reporter_pipe concat_step2_records` with at least two `--records`
paths and `--output`. Headers must match exactly. Do not use `zcat`: it keeps
every input header unless you strip later headers by hand. See
[`concat_step2_records`](cli/pipe.md#concat_step2_records).

## Do QC plots gate the pipeline?

No. QC is inspection-only. It does not apply pass/fail thresholds and does not
modify pipeline artifacts.

## Where are the current release limitations?

See [Known limitations](known-limitations.md) for external-tool versioning and
release-validation boundaries in 0.1.0b3.
