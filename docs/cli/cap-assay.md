# `cap-assay-pipeline`

Command-line entrypoint for the four-step **cap-selection** workflow (QUASARR-cap
and related assays). It is registered additively with the reporter-assay
executables and does not change `yulab_reporter_pipe` behavior.

```text
Process cap-selection assay sequencing data into strand-specific RNA endpoint bigWig tracks.
```

This page documents the released **0.1.0b3** contract. `cap-assay-pipeline --help`
and `cap-assay-pipeline <step> --help` describe the installed local build.

See [Cap-selection workflow](../cap-selection/workflow.md) for fork–join topology
and distinction from the reporter-assay pipeline.

## Installation dependencies

Installing the `reporter-assay-pipeline` distribution adds the `cap-assay-pipeline`
executable alongside the reporter-assay commands (same package version as
`cap-assay-pipeline --version`).

| Step | External tools (minimum versions where probed) |
| --- | --- |
| 1 | `fastp` (not version-pinned by the package) |
| 2 | (layout-driven; see step help) |
| 3 | STAR **2.7.0+**, samtools **1.10+**, `zcat` on `PATH` |
| 4 | samtools **1.12+**, BEDTools **2.30+**; **pyBigWig** is a Python dependency |

Record external tool versions in each step summary JSON. Step 4 resolves
`samtools` and `bedtools` from `--samtools` / `--bedtools` or `PATH`, probes
`--version` before processing, and stores accepted version strings in the
summary when known.

Verify registration:

```bash
cap-assay-pipeline --version
cap-assay-pipeline --help
```

## Top-level commands

Exactly four subcommands are registered, in numeric order:

| Command | Summary |
| --- | --- |
| `step1-prep-fastq` | Prepare reads with fastp (trim, R1 UMI in names, filter; UMI-aware dedup in Step 4) |
| `step2-build-reference` | Build construct-derived reference FASTA |
| `step3-alignment` | Align one library to one reference; publish BAM + BAI + summary |
| `step4-post-alignment-processing` | Four strand-specific RNA endpoint bigWigs from one library BAM |

Unknown top-level commands and options are rejected before any step module
loads. After a recognized command, all remaining tokens are forwarded to that
step’s parser.

### Exit statuses (package boundary)

| Outcome | Typical status |
| --- | --- |
| Success | `0` (no stdout payload for operational steps) |
| Step validation, tool, integrity, or publication failure | `1` (concise message on stderr) |
| Step usage / argument errors | `2` (stderr) |
| Top-level help or `--version` | `0` (stdout) |
| No subcommand | non-zero (help on stderr) |

Individual steps follow the table above for their owned parsers.

---

## `step4-post-alignment-processing`

Processes **exactly one** coordinate-sorted library BAM per invocation into
four signed bigWig tracks and one summary. This is the cap-selection **Step 4**
endpoint; it is unrelated to reporter-assay `yulab_reporter_pipe step4` (PreTran
count merging).

### Required arguments

| Flag | Meaning |
| --- | --- |
| `--library-prefix` | Filename-safe token `[A-Za-z0-9][A-Za-z0-9._-]*` (not `.` or `..`); must match the sole `@RG` ID in the BAM |
| `--input-bam` | Readable, non-empty coordinate-sorted BAM |
| `--output-dir` | Directory that will receive the five published artifacts (created when possible) |

### Optional arguments

| Flag | Default | Meaning |
| --- | --- | --- |
| `--threads` | `16` | Positive integer; worker threads for samtools |
| `--max-pair-mismatches` | `4` | Non-negative integer; **inclusive** ceiling on `NM(R1) + NM(R2)` |
| `--samtools` | `samtools` | samtools executable path or name |
| `--bedtools` | `bedtools` | BEDTools executable path or name |

There is no reference path, BAI input, project root, overwrite flag, batch mode,
normalization control, or generic passthrough to native tool CLIs. Native
samtools and BEDTools streams are captured internally, not exposed as the user
interface.

### BAM-only compatibility boundary

Step 4 admits structurally compatible **BAM** evidence only:

- Regular, readable, non-empty file; `samtools quick-check` succeeds
- Header `SO:coordinate`; records coordinate-ordered per `@SQ` order
- Unique `@SQ` names with positive lengths; order preserved in outputs
- Exactly one `@RG` with `ID` equal to `--library-prefix`
- Every alignment record has `RG` matching that ID

No BAI, external reference FASTA, or chromosome-size file is required. Step 3
provenance is not required when an external BAM satisfies the rules above.

**Not accepted as substitutes:** SAM, CRAM, split R1/R2 tables, or multi-library
BAMs merged under several read groups.

### Pair-level filtering

Filtering is **pair-aware**: R1 and R2 are assessed together per query name.
The pipeline does **not** perform barcode error correction or UMI-aware
rescuing; Step 1 UMI annotation is not reinterpreted here.

For each query name, records are name-collated. Exactly one primary R1 and one
primary R2 must be present; duplicate primary mates for the same end fail the
invocation.

An eligible pair must satisfy all of the following (first failing rule wins
for rejection accounting):

| Order | Rejection reason | Rule |
| --- | --- | --- |
| 1 | `excluded_flags` | Either mate has unmapped, secondary, supplementary, QC-fail, or duplicate flag |
| 2 | `mapping_completeness` | Not exactly one primary R1 and one primary R2 |
| 3 | `uniqueness` | `NH != 1` on either mate |
| 4 | `cigar` | CIGAR must be full-query `M`, `=`, or `X` only (no clipping, indels, or skipped regions) |
| 5 | `mismatch_ceiling` | `NM(R1) + NM(R2) > --max-pair-mismatches` (equality retains the pair) |
| 6 | `geometry` | Same reference; opposite strands; R1/R2 5′ positions ordered consistently with R2 as RNA 5′ and R1 as RNA 3′ |

Each eligible pair contributes one R2 **cap signal** observation (sequenced 5′
of R2) and one R1 **polymerase-position proxy** observation (sequenced 5′ of
R1, antisense to nascent RNA, inverted to biological RNA strand). **R2 3′
endpoints are not consumed.**

**Zero eligible pairs** after filtering is a failed invocation (`status: failed`
in `{prefix}.step4_summary.json` when written). Success and failure summaries
both publish reconciled `pair_total_groups`, `eligible_pairs`, `rejected_pairs`,
`rejection_counts`, and `mismatch_histogram` when pair auditing completed.

### Published artifacts

On success, exactly these files appear directly under `--output-dir` (`S` =
library prefix):

```text
S.5pl.bw
S.5mn.bw
S.3pl.bw
S.3mn.bw
S.step4_summary.json
```

Encoding details: [cap-selection Step 4 bigWig tracks](../formats.md#cap-selection-step-4-bigwig-tracks)
and [step 4 summary](../formats.md#cap-selection-step-4-summary-json).

### Concurrent runs and collisions

Step 4 acquires `.{prefix}_step4.lock` in the output directory for the
invocation. The five target paths (including symlinks) must be absent before
processing; existing outputs are not overwritten. A cooperating second
invocation with the same prefix and directory receives an already-active error.

### Complete runnable example

After [Step 3](../cap-selection/steps-1-3.md#step-3-alignment) produced
`aligned/LIB01_step3_alignment.bam`:

```bash
cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix LIB01 \
  --input-bam aligned/LIB01_step3_alignment.bam \
  --output-dir tracks/ \
  --threads 16 \
  --max-pair-mismatches 4 \
  --samtools samtools \
  --bedtools bedtools
```

Expect exit code `0`, no stdout, five new files under `tracks/`, and
`tracks/LIB01.step4_summary.json` with `"status": "success"`. Observation
totals reconcile: `track_observations.cap_plus + track_observations.cap_minus`
and the proxy pair each equal `eligible_pairs`.

### Help

```bash
cap-assay-pipeline step4-post-alignment-processing --help
```

Help prints on stdout with exit `0` without validating paths, resolving tools,
or running external commands. It documents the flags above, BAM admission,
tool minimums, endpoint meanings, track filenames, zero-eligible failure, and
the example invocation.

---

## Steps 1–3 (summary)

Operational detail for the fork legs is in [Steps 1–3](../cap-selection/steps-1-3.md).
Invoke help per step:

```bash
cap-assay-pipeline step1-prep-fastq --help
cap-assay-pipeline step2-build-reference --help
cap-assay-pipeline step3-alignment --help
```
