# Steps 1–2: prepare one library

This page is the canonical procedure for running and checking the first two
pipeline stages for one library in release **0.1.0b2**. Use it when you need
to run or resume individual stages. For input checks and schema construction,
see [Prepare inputs](input-preparation.md) and [Layout schemas](layout-schemas.md).
For the equivalent grouped command, see [`prep_lib`](cli/pipe.md#prep_lib-step1-step2).

## What the handoff does

Step 1 uses one raw paired FASTQ input to produce a cleaned paired FASTQ. The
configured cleaner is `fastp` by default; it performs paired-end adapter and
quality cleanup and rejects reads that fail its validity checks. Step 1 keeps
R1/R2 synchronized and writes cleaner reports.

Step 2 reads that cleaned pair and a library-specific layout schema. It walks
R1 and R2 in lockstep, checks constant anchors, captures fields in schema
order, applies configured reverse complements after extraction, and writes one
tab-delimited row for each retained pair. The resulting
`delimited-records` file is consumed by Step 3 for PreTran libraries or Step 6
for post-transfection libraries.

Each command handles exactly one `--library-prefix`. Repeat the procedure for
each `PreTran_CW`, `PreTran_CCW`, `eBC_*`, and `pBC_*` library required by the
selected profile. Keep the same prefix through input names, summaries, and
downstream commands.

## Prerequisites

Before Step 1, complete the [paired FASTQ checks](input-preparation.md#paired-fastq-checks).
Both files must be readable, non-empty, gzip-valid FASTQ files with equal,
pair-synchronized record counts. Do not use Step 1 to repair a corrupt or
mispaired input.

Before Step 2, validate the library-specific [layout schema](layout-schemas.md).
It must contain `layout1`, `layout2`, and ordered `column_names`; any named
`reverse_complements` field must be one of those columns. The schema must match
the library's read layout and branch. A valid schema is not interchangeable
with another branch merely because the files have the same suffixes.

Install the documented `0.1.0b2` package and put `fastp` on `PATH`. The
documentation does not pin the external `fastp` version; record the binary
used by your environment when reproducibility matters.

## Run Step 1

Run this command from any directory. Replace placeholders with local paths;
the names and prefixes are intentionally generic.

```bash
yulab_reporter_pipe step1 \
  --library-prefix eBC_DNA_rep1 \
  --input-r1 "<raw_dir>/eBC_DNA_rep1_R1.fastq.gz" \
  --input-r2 "<raw_dir>/eBC_DNA_rep1_R2.fastq.gz" \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work/trimmed" \
  --threads 16 \
  --cleaner fastp
```

The installed individual-step help may not expose the complete released
surface in `0.1.0b2`; use this versioned procedure as the contract and see the
[known limitations](known-limitations.md#individual-step-help-is-incomplete)
for the documented discrepancy.

The command exits successfully only when the cleaner exits zero and the
cleaned output can be read. Step 1 validates required argument shape and
path-like inputs before invoking the cleaner. A missing cleaner, unreadable or
corrupt FASTQ, unequal pairing, or non-zero cleaner exit is fatal for this
invocation. A failed library does not invalidate other library directories,
but the workflow is incomplete until this library is repaired and rerun.

### Step 1 artifacts

All paths below are relative to `<project_dir>/work/trimmed` unless an explicit
`--output-dir` was supplied.

| Artifact | Producer | Consumer or use |
| --- | --- | --- |
| `<prefix>_R1.trim.fq.gz` | Step 1 | Step 2 `--input-r1`; retain when resuming |
| `<prefix>_R2.trim.fq.gz` | Step 1 | Step 2 `--input-r2`; retain when resuming |
| `<prefix>_fastp.html` | `fastp` via Step 1 | Human diagnostic report |
| `<prefix>_fastp.json` | `fastp` via Step 1 | Machine-readable cleaner report |
| `<prefix>_step1_summary.json` | Step 1 | Completion and recovery evidence |

The summary is JSON and includes `library_prefix`, `input_r1`, `input_r2`,
`output_r1`, `output_r2`, `fastp_html`, `fastp_json`,
`input_read_pairs`, `output_read_pairs`, `status`, and `failure_reason`.
`status` is `success` or `failed`; a failed summary explains the invocation
failure. The two output FASTQs must exist and have synchronized pair counts.

```bash
test -s "<project_dir>/work/trimmed/eBC_DNA_rep1_R1.trim.fq.gz"
test -s "<project_dir>/work/trimmed/eBC_DNA_rep1_R2.trim.fq.gz"
jq '{status, input_read_pairs, output_read_pairs, failure_reason}' \
  "<project_dir>/work/trimmed/eBC_DNA_rep1_step1_summary.json"
gzip -t "<project_dir>/work/trimmed/eBC_DNA_rep1_R1.trim.fq.gz"
gzip -t "<project_dir>/work/trimmed/eBC_DNA_rep1_R2.trim.fq.gz"
```

Proceed to Step 2 only when the summary says `status: "success"`, both output
paths are present, and `output_read_pairs` is non-zero and synchronized.

## Run Step 2

Use the exact Step 1 output paths as Step 2 inputs. This explicit handoff is
equivalent to the wiring performed by `prep_lib`.

```bash
yulab_reporter_pipe step2 \
  --library-prefix eBC_DNA_rep1 \
  --input-r1 "<project_dir>/work/trimmed/eBC_DNA_rep1_R1.trim.fq.gz" \
  --input-r2 "<project_dir>/work/trimmed/eBC_DNA_rep1_R2.trim.fq.gz" \
  --layout-schema "<schemas>/ebc_layout.json" \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work/delimited" \
  --threads 16 \
  --max-edit-distance 1 \
  --min-last-anchor-match 10
```

For each synchronized pair, a constant-anchor mismatch, extraction overrun,
or failed terminal-anchor match is a tolerated **record-level extraction
mismatch**: the pair is skipped and counted. It is not, by itself, an
invocation failure. A malformed or unreadable schema, corrupt FASTQ,
R1/R2 desynchronization, unwritable output, zero input pairs, or zero retained
records is invocation-fatal. The terminal partial-match rule applies only to
the final anchor and requires at least `min-last-anchor-match` overlapping
bases within `max-edit-distance` mismatches.

### Step 2 artifacts

All paths below are relative to `<project_dir>/work/delimited` unless an
explicit `--output-dir` was supplied.

| Artifact | Producer | Consumer or use |
| --- | --- | --- |
| `<prefix>_step2_records.tsv.gz` | Step 2 | Step 3 (`PreTran`) or Step 6 (post-transfection) |
| `<prefix>_step2_summary.json` | Step 2 | Completion, mismatch diagnosis, and handoff evidence |

The records file has a required tab-delimited header exactly equal to schema
`column_names`, in order. Captures are assigned across `layout1` then
`layout2`; only fields named in `reverse_complements` are transformed. The
summary includes `library_prefix`, `input_r1`, `input_r2`, `layout_schema`,
`output_records_path`, ordered `output_columns`, `input_read_pairs`,
`output_record_count`, `mismatch_record_count`, `mismatch_percentage`,
`status`, and `failure_reason`.

```bash
gzip -cd "<project_dir>/work/delimited/eBC_DNA_rep1_step2_records.tsv.gz" \
  | sed -n '1,3p'
jq '{status, input_read_pairs, output_record_count,
    mismatch_record_count, mismatch_percentage, output_columns,
    failure_reason}' \
  "<project_dir>/work/delimited/eBC_DNA_rep1_step2_summary.json"
```

Completion requires `status: "success"`, a non-empty records file, a header
matching the schema's ordered columns, and internally consistent mismatch
counts. A non-zero mismatch count can still be a successful run when at least
one record remains; inspect the percentage rather than treating every skipped
pair as fatal.

## Symptom-first recovery

| Symptom or summary evidence | Classification | Next valid action |
| --- | --- | --- |
| Step 1 summary is `failed`; `failure_reason` names a missing cleaner or non-zero cleaner exit | Invocation-fatal prerequisite/tool failure | Install or select the intended cleaner, fix the reported input, and rerun Step 1 for this prefix |
| Step 1 outputs are absent, unreadable, or pair counts differ | Invocation-fatal output/integrity failure | Retain the raw inputs and Step 1 summary for diagnosis; correct the cleaner/input and rerun Step 1 before Step 2 |
| Step 2 cannot load schema or reports missing keys/unknown reverse-complement field | Invocation-fatal configuration failure | Repair the schema for this library; rerun Step 2 using retained Step 1 FASTQs |
| Step 2 `mismatch_record_count` is non-zero but `status` is `success` and `output_record_count` > 0 | Tolerated record-level extraction mismatches | Inspect anchors, trimming, direction, and mismatch percentage; continue only with the retained records if the loss is understood |
| Step 2 reports pair synchronization, corrupt FASTQ, or unwritable output | Invocation-fatal integrity/I/O failure | Preserve retained Step 1 outputs and summaries, repair or regenerate the affected asset, then rerun Step 2 |
| Step 2 `output_record_count` is zero | Fatal zero-output condition | Keep the schema, Step 1 artifacts, and Step 2 summary; correct schema/anchors/read direction or trimming, then rerun Step 2 |
| Grouped `prep_lib` removed Step 1 intermediates after success | Expected retention policy | Rerun with `--no-delete-intermediate` when debugging; otherwise use retained summaries and rerun Step 1 if Step 2 must be repeated |

Do not continue to Step 3 or Step 6 from a failed summary. After a successful
Step 2, use the retained records path shown in its summary and follow the
[workflow handoff](workflow.md) for the library's branch and orientation.
