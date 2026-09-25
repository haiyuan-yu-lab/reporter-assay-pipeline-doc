# `cap-assay-pipeline`

Command-line entrypoint for the four-step **cap-selection** workflow (QUASARR-cap
and related assays). It is registered additively with the reporter-assay
executables and does not change `yulab_reporter_pipe` behavior.

```text
Process cap-selection assay sequencing data into strand-specific RNA endpoint bigWig tracks.
```

This page documents the released **0.2.0b1** contract. `cap-assay-pipeline --help`
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
| 4 | samtools **1.12+**, BEDTools **2.30+**, UMI-tools; **pyBigWig** is a Python dependency |

Record external tool versions in each step summary JSON. Step 4 resolves
`samtools`, `bedtools`, and `umi_tools` from their step options or `PATH`, probes
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
| `step2-build-reference` | Build construct-derived reference FASTA (unique complete sequence per Element) |
| `step3-alignment` | Align one library to one reference; publish BAM + BAI + summary |
| `step4-post-alignment-processing` | Strand-selected RNA endpoint bigWigs from one library BAM (four tracks for `both`, two for `plus`/`minus`) |

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
strand-selected signed bigWig tracks and one summary: four tracks for the
default `--rna-strand both`, cap-plus/proxy-plus for `plus`, cap-minus/
proxy-minus for `minus`. This is the cap-selection **Step 4**
endpoint; it is unrelated to reporter-assay `yulab_reporter_pipe step4` (PreTran
count merging).

### Required arguments

| Flag | Meaning |
| --- | --- |
| `--library-prefix` | Filename-safe token `[A-Za-z0-9][A-Za-z0-9._-]*` (not `.` or `..`); must match the sole `@RG` ID in the BAM |
| `--input-bam` | Readable, non-empty coordinate-sorted BAM |
| `--output-dir` | Directory that will receive the published artifacts (created when possible): five files for `both`, three for `plus`/`minus` |

### Optional arguments

| Flag | Default | Meaning |
| --- | --- | --- |
| `--threads` | `16` | Positive integer; worker threads for samtools |
| `--max-pair-mismatches` | `4` | Non-negative integer; **inclusive** ceiling on `NM(R1) + NM(R2)` |
| `--samtools` | `samtools` | samtools executable path or name |
| `--bedtools` | `bedtools` | BEDTools executable path or name |
| `--umi-dedup-method` | `directional` | UMI-tools `dedup --method` (`unique`, `percentile`, `cluster`, `adjacency`, `directional`) |
| `--umi-tools` | `umi_tools` | UMI-tools executable path or name |
| `--rna-strand` | `both` | Expected reference-relative biological RNA strand (`both`, `plus`, `minus`); also selects the published track set |

There is no reference path, BAI input, project root, overwrite flag, batch mode,
no-deduplication mode, or generic passthrough to native tool CLIs. Native
samtools, BEDTools, and UMI-tools streams are captured internally, not exposed
as the user interface.

### BAM-only compatibility boundary

Step 4 admits structurally compatible **BAM** evidence only:

- Regular, readable, non-empty file; `samtools quick-check` succeeds
- Header `SO:coordinate`; records coordinate-ordered per `@SQ` order
- Unique `@SQ` names with positive lengths; order preserved in outputs
- Exactly one `@RG` with `ID` equal to `--library-prefix`
- Every alignment record has `RG` matching that ID

No BAI, external reference FASTA, or chromosome-size file is required. Step 3
provenance is not required when an external BAM satisfies the rules above.

Every query name must end with the canonical fastp-produced UMI suffix:
`:UMI_` followed by exactly twelve uppercase `A`, `C`, `G`, or `T` bases
on both mates (the first whitespace-delimited identifier carries the
suffix, as emitted by the supported Step 1 fastp configuration). Missing,
malformed (including the former `_UMI:` spelling), or `N`-bearing UMI
evidence fails the invocation before pair filtering, UMI-tools
deduplication, or track publication; there is no mode that
skips UMI deduplication.

**Not accepted as substitutes:** SAM, CRAM, split R1/R2 tables, or multi-library
BAMs merged under several read groups.

### Pair-level filtering

Filtering is **pair-aware**: R1 and R2 are assessed together per query name.
Eligibility runs **before** UMI-tools paired deduplication so rejected pairs
cannot affect molecule grouping.

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

**RNA strand assertion:** `--rna-strand` declares the expected
reference-relative biological RNA strand, determined by R2's BAM strand. It
is an assertion, not a filter: with `plus` or `minus`, any otherwise
eligible pair whose R2 lies on the opposite strand fails the invocation
before UMI-tools deduplication with its contradictory-pair count, and no
tracks are published. Pairs rejected by ordinary filters never count as
contradictory. Pass the same `--rna-strand` value to Steps 3 and 4; a
permissive mismatch (selected-strand BAM passed as `both`) publishes extra
empty tracks. Complete unmapped primary pairs without mapped-placement tags
(Step 3 strand-rejected evidence) are admitted and audit as ordinary
unmapped pairs.

Eligible pairs are written to a staging BAM and deduplicated with UMI-tools
`dedup --paired` using `--umi-dedup-method` (default `directional`). Track
counts use **retained** pairs after deduplication.

**Zero eligible pairs** after filtering or **zero retained pairs** after UMI
deduplication is a failed invocation (`status: failed` in
`{prefix}.step4_summary.json` when written). Success and failure summaries
publish reconciled `pair_total_groups`, `eligible_pairs`,
`pre_dedup_eligible_pairs`, `umi_duplicate_pairs_removed`, `rejected_pairs`,
`rejection_counts`, and `mismatch_histogram` when pair auditing completed,
with `pre_dedup_eligible_pairs = eligible_pairs + umi_duplicate_pairs_removed`
and `pair_total_groups = rejected_pairs + pre_dedup_eligible_pairs`.

### Published artifacts

On success, exactly these files appear directly under `--output-dir` (`S` =
library prefix):

```text
both:  S.5pl.bw S.5mn.bw S.3pl.bw S.3mn.bw S.step4_summary.json
plus:  S.5pl.bw S.3pl.bw S.step4_summary.json
minus: S.5mn.bw S.3mn.bw S.step4_summary.json
```

Policy-omitted tracks are absent (not header-only). Under `both`, selected
tracks with no observations still publish real header-only bigWigs. The
summary always retains all four track keys; omitted tracks carry `null`
paths/hashes and zero metrics.

Encoding details: [cap-selection Step 4 bigWig tracks](../formats.md#cap-selection-step-4-bigwig-tracks)
and [step 4 summary](../formats.md#cap-selection-step-4-summary-json).

### Concurrent runs and collisions

Step 4 acquires `.{prefix}_step4.lock` in the output directory for the
invocation. Only the selected track paths plus the summary must be absent
before processing (five paths for `both`, three for `plus`/`minus`);
existing outputs for omitted strands are unrelated files and are neither
checked nor removed. A cooperating second
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
totals reconcile per selected policy: under `both`,
`track_observations.cap_plus + track_observations.cap_minus`
and the proxy pair each equal `eligible_pairs`; under `plus`, `cap_plus`
and `proxy_plus` each equal `eligible_pairs` (mirrored for `minus`).

### Help

```bash
cap-assay-pipeline step4-post-alignment-processing --help
```

Help prints on stdout with exit `0` without validating paths, resolving tools,
or running external commands. It documents the flags above, BAM admission,
tool minimums, endpoint meanings, track filenames, zero-eligible failure, and
the example invocation.

---

## `step2-build-reference`

Builds the four-file construct-derived reference bundle from a version-one
construct-layout JSON and a tested-element FASTA. Each Element must produce a
unique normalized complete constructed sequence; duplicates across distinct
Elements exit `1` with a failed summary (`shared_sequence_count` reports collision
groups) and no successful FASTA, annotations, or manifest. Successful bundles
set `shared_sequence_count` to zero in the manifest and summary.

Required flags: `--reference-prefix`, `--construct-layout`, `--tested-elements`,
`--output-dir`. See `cap-assay-pipeline step2-build-reference --help` for the
layout grammar, FASTA rules, artifact names, and example invocation.

---

## Steps 1–3 (summary)

Operational detail for the fork legs is in [Steps 1–3](../cap-selection/steps-1-3.md),
including Step 3 `--rna-strand {both,plus,minus}` (default `both`) selection,
strand-rejected unmapped retention, and `effective_mapping_counts`.
Invoke help per step:
```bash
cap-assay-pipeline step1-prep-fastq --help
cap-assay-pipeline step2-build-reference --help
cap-assay-pipeline step3-alignment --help
```
