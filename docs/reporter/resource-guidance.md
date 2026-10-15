# Reporter resource guidance

This page describes operator-facing CPU controls in release **0.2.0b4**.
`--threads` sets the CPU budget for one invocation; a phase can use fewer
workers when its work is serial or bounded by input structure. Defaults are
preserved from the release.

| Command group | Default | Operator guidance |
| --- | ---: | --- |
| Reporter Steps 1–2 and `prep_lib` | 16 | `prep_lib` reuses its selected budget for Step 1 and then Step 2. `fastp` receives the Step 1 worker count. |
| Reporter Step 3 | 1 | Bounded row chunks use at most `threads - 1` worker processes plus the parent. Grouped dual-orientation PreTran divides a budget above one between CW and CCW. |
| Reporter Steps 4–5 | 1 | The grouped PreTran invocation reuses its selected budget; global aggregation and graph reconciliation remain necessary. |
| Reporter Steps 6–8 and `process_posttrans` | 1 | One selected budget is reused sequentially for a replicate's three steps. Independent replicate invocations can be scheduled separately by the operator. |
| Reporter Step 9 and `call_activity` | 1 | Independent input tables can be prepared with bounded workers; normalization, model fitting, and control baseline remain global to each branch call. |
| Reporter QC | 1 | Between-replicate and orientation plotting commands expose `--threads`; other single-source plots run serially. |
| `yulab_reporter_export` | 1 | Independent reference FASTAs can be prepared concurrently within the selected budget; final validation and publication are coordinated. |

## Dependencies and flags

Install `fastp` separately for reporter library preparation. Step 9 requires
`Rscript` with edgeR and limma; three-or-more-pair fits also require
`statmod`. QC uses the package's `pandas` and `matplotlib` dependencies, and
QC/export are installed with `pip install .`. Use `--threads` on the commands
listed above where supported; each command page documents its default and
accepted values.

Use `--threads 1` for serial execution where supported. More threads do not
promise a fixed wall-clock speedup: input size, distinct identifiers, model
work, and serial phases affect runtime and memory. `fastp`, R/BLAS, and other
external libraries can have their own resource behavior. See each [pipeline
CLI](../cli/pipe.md), [QC CLI](../cli/qc.md), and [export CLI](../cli/export.md)
for the commands that expose the flag.
