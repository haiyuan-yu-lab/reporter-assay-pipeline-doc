# `cap-assay-pipeline`

Command-line entrypoint for the four-step **cap-selection** workflow (QUASARR-cap
and related assays). It is registered additively with the reporter-assay
executables and does not change `yulab_reporter_pipe` behavior.

```text
Process cap-selection assay sequencing data into strand-specific RNA endpoint bigWig tracks.
```

This page documents the released **0.2.0b5** native barcode-directed
interface. Step 2 identification is mandatory, Step 3 aligns each pair to the
Element selected by its barcode, and STAR is not used. Upgrading from an
earlier release is a breaking change; see [Migrating to
0.2.0b5](../cap-selection/migrating-to-0.2.0b5.md). `cap-assay-pipeline --help`
and `cap-assay-pipeline <step> --help` describe the installed local build.

See [Cap-selection workflow](../cap-selection/workflow.md) for the step
topology and the distinction from the reporter-assay pipeline.

## Installation dependencies

Installing the `reporter-assay-pipeline` distribution adds the `cap-assay-pipeline`
executable alongside the reporter-assay commands (same package version as
`cap-assay-pipeline --version`).

| Step | External tools (minimum versions where probed) |
| --- | --- |
| 1 | `fastp` (not version-pinned by the package) |
| 2 | None |
| 3 | samtools **1.10+** |
| 4 | samtools **1.12+**, BEDTools **2.30+**, UMI-tools; **pyBigWig** is a Python dependency |

STAR is not a dependency. Step 3 resolves `samtools` from `--samtools` or
`PATH` and probes `--version` before processing reads. Step 4 resolves
`samtools`, `bedtools`, and `umi_tools` from their step options or `PATH`,
probes `--version` before processing, and stores accepted version strings in
the summary when known.

Verify registration:

```bash
cap-assay-pipeline --version
cap-assay-pipeline --help
```

## Top-level commands

Four subcommands are registered, in workflow order:

| Command | Summary (from `--help`) |
| --- | --- |
| `step1-prep-fastq` | Prepare cap-selection reads with fastp (trim, R1 UMI in names, filter; UMI-aware dedup in Step 4). |
| `step2-identify-and-clip` | Identify named CAP fields and retain configured read intervals before alignment. |
| `step3-alignment` | Map annotated read pairs to element references using barcode identity, substitutions, and internal indels. |
| `step4-post-alignment-processing` | Produce strand-selected RNA endpoint bigWig tracks from one library BAM. |

Unknown top-level commands and options are rejected before any step module
loads; the removed `step2-clip-construct-flank` command is rejected as an
invalid command. After a recognized command, all remaining tokens are
forwarded to that step's parser. There is no grouped whole-pipeline command.

### Exit statuses (package boundary)

| Outcome | Typical status |
| --- | --- |
| Success | `0` (no stdout payload for operational steps) |
| Step validation, tool, integrity, or publication failure | `1` (concise message on stderr) |
| Step usage / argument errors, including removed options | `2` (stderr) |
| Top-level help or `--version` | `0` (stdout) |
| No subcommand | non-zero (help on stderr) |

---

## `step1-prep-fastq`

```text
usage: cap-assay-pipeline step1-prep-fastq [-h] --library-prefix
                                           LIBRARY_PREFIX --input-r1 INPUT_R1
                                           --input-r2 INPUT_R2 --output-dir
                                           OUTPUT_DIR [--threads THREADS]
                                           [--fastp FASTP]
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--library-prefix`, `--input-r1`, `--input-r2`, `--output-dir` | required | Library token, raw paired FASTQs, and output directory |
| `--threads` | `16` | CPU budget for bounded Python workers and the separate fastp phase |
| `--fastp` | `fastp` | fastp executable |

Step 1 is unchanged in this release. It trims adapters, moves the 12-base R1
UMI into both read names as `:UMI_<12 A/C/G/T>`, excludes pairs whose UMI
contains `N`, and publishes `{prefix}_R1.trim.fq.gz`, `{prefix}_R2.trim.fq.gz`,
and `{prefix}_step1_summary.json`. Python validation and ambiguous-UMI
exclusion use bounded chunks and at most N−1 worker processes plus the parent;
N=1 uses direct execution. Fastp runs separately with `-w N` and may create
fixed reader/writer threads beyond that flag. See
[Steps 1–3](../cap-selection/steps-1-3.md#step-1-prepare-fastq).

---

## `step2-identify-and-clip`

Mandatory Step 2. It matches the CAP layout against each prepared pair,
extracts normalized named captures, retains one contiguous interval from each
mate, and carries the captures in the read names for Step 3.

```text
usage: cap-assay-pipeline step2-identify-and-clip [-h] --library-prefix
                                                  LIBRARY_PREFIX --input-r1
                                                  INPUT_R1 --input-r2 INPUT_R2
                                                  --layout LAYOUT --output-dir
                                                  OUTPUT_DIR
                                                  [--min-retained-length MIN_RETAINED_LENGTH]
                                                  [--max-anchor-mismatches MAX_ANCHOR_MISMATCHES]
                                                  [--threads THREADS]
                                                  [--gzip-compression-level 0–9]
```

### Arguments

| Flag | Default | Meaning |
| --- | --- | --- |
| `--library-prefix` | required | Filename-safe token `[A-Za-z0-9][A-Za-z0-9._-]*` (not `.` or `..`) |
| `--input-r1`, `--input-r2` | required | Gzip paired FASTQs from Step 1 (or a compatible source) carrying matching `:UMI_<12 A/C/G/T>` suffixes |
| `--layout` | required | CAP layout JSON, schema version 1 ([format](../cap-selection/formats.md#step-2-layout-json-schema-version-1)) |
| `--output-dir` | required | Output directory (created when possible) |
| `--min-retained-length` | `15` | Positive integer; minimum retained bases for **each** mate |
| `--max-anchor-mismatches` | `1` | Non-negative integer; default substitution ceiling per fixed anchor (a segment's `max_mismatches` overrides it) |
| `--threads` | `1` | Positive CPU budget; at most `threads - 1` worker processes evaluate bounded chunks of 256 pairs while the parent reads, merges in input order, and publishes |
| `--gzip-compression-level` | `1` | 0 (fastest, largest) through 9 (slowest, smallest) for the identified FASTQs |

The layout is validated before any read is processed. Fixed anchors match
completely at their computed positions, permitting substitutions only; there
is no scanning for alternative positions, partial anchors, or anchor indels,
and `N` counts as a mismatch. Captures are checked against their alphabet,
then normalized; normalization affects capture metadata only, never the
retained sequence or qualities. Repeated captures with the same name must
agree after normalization. Each layout is evaluated once per pair; a pair is
retained only when exactly one layout succeeds.

Each retained mate's first name token receives the reserved annotation
`|CAP1=<payload>` immediately before its unchanged `:UMI_` suffix. The payload
is unpadded URL-safe base64 of canonical JSON (sorted keys, no whitespace)
mapping every capture name to its normalized value. Both mates carry the same
object. A name that would exceed SAM's 254-character QNAME limit fails the
invocation rather than being truncated.

### Outputs

```text
LIB01_R1.ident.fq.gz
LIB01_R2.ident.fq.gz
LIB01_step2_rejected_R1.fq.gz
LIB01_step2_rejected_R2.fq.gz
LIB01_step2_rejections.tsv.gz
LIB01_step2_summary.json
```

Rejected FASTQs contain the original input pairs. The rejection table and
summary are described in the [format contracts](../cap-selection/formats.md#step-2-outputs-and-summary).
Each processed pair is rejected for exactly one primary reason:
`anchor_or_length_mismatch`, `invalid_capture`,
`disagreeing_repeated_capture`, `short_retained_mate`, or
`multiple_successful_layouts`.

Zero retained pairs is a failure; rejection artifacts and a failed summary are
still written. If processing stops midstream, rejection evidence for the
evaluated pairs is retained, the summary records `complete: false`, and no
identified FASTQs are published. An invalid layout or other configuration
error fails before processing without a summary. Every output path must be
absent; a per-prefix lock serializes concurrent invocations.

---

## `step3-alignment`

Resolves selected named captures by exact barcode lookup, then aligns the
paired reads to the one selected Element on the declared RNA strand.

```text
usage: cap-assay-pipeline step3-alignment [-h] --library-prefix LIBRARY_PREFIX
                                          --input-r1 INPUT_R1 --input-r2
                                          INPUT_R2 --reference REFERENCE
                                          --barcode-map BARCODE_MAP
                                          --barcode-field NAME --output-dir
                                          OUTPUT_DIR [--threads THREADS]
                                          [--max-pair-edits MAX_PAIR_EDITS]
                                          --rna-strand {plus,minus}
                                          [--samtools SAMTOOLS]
                                          [--bam-sort-memory BAM_SORT_MEMORY]
                                          [--tmp-dir TMP_DIR]
```

### Arguments

| Flag | Default | Meaning |
| --- | --- | --- |
| `--library-prefix` | required | Filename-safe token; becomes the BAM read-group ID |
| `--input-r1`, `--input-r2` | required | Gzip paired FASTQs carrying a well-formed CAP1 annotation and matching UMI suffix (normally the Step 2 `.ident.fq.gz` outputs) |
| `--reference` | required | Element-only FASTA |
| `--barcode-map` | required | CAP-owned barcode/Element TSV |
| `--barcode-field NAME` | required, repeatable | Capture name to use for identity lookup; give at least one, each distinct |
| `--rna-strand` | required (`plus` or `minus`) | Reference-relative biological RNA strand to search; there is no default and no `both` |
| `--output-dir` | required | Output directory (created when possible) |
| `--threads` | `16` | Positive CPU budget for ordered pair-batch workers and `samtools sort` |
| `--max-pair-edits` | `4` | Non-negative inclusive ceiling on substituted + inserted + deleted bases, combined across both mates |
| `--samtools` | `samtools` | samtools executable path or name (1.10+) |
| `--bam-sort-memory` | `2G` | Aggregate `samtools sort` memory, as bytes or an integer with `K`, `M`, or `G`; divided across sorting threads and must give at least 1 MiB per thread |
| `--tmp-dir` | invocation-local | Existing writable directory for sort intermediates |

The STAR-era options `--star`, `--star-index-dir`, `--max-multimaps`, and
`--random-seed` are removed and are rejected as unrecognized arguments
(exit `2`). `--rna-strand both` is an invalid choice at Step 3.

### Input admission

Before any read is processed, Step 3 validates the complete reference and
barcode map:

- **Reference FASTA:** unique non-empty first-token IDs; non-empty sequences of
  A/C/G/T/N (normalized to uppercase). Unused records and identical sequences
  under different IDs are allowed. No sidecars, manifests, or index are used.
- **Barcode map:** UTF-8 TSV with unique column names including `barcode` and
  `Element`; other columns are ignored. Barcodes are uppercase A/C/G/T.
  Duplicate identical rows coalesce; a barcode assigned to two Elements, or an
  `Element` absent from the FASTA, fails the invocation. Every row is
  validated, including unused rows.

For each pair, every selected field must be present and contain A/C/G/T, and
the exact lookups must all resolve to the same Element. Other captures are
carried as metadata only. A malformed CAP1 annotation, a missing selected
field, or mate annotation/name/UMI disagreement fails the invocation; it is
not counted as a read-level rejection.

### Native alignment

Each pair is aligned only against the sequence of its resolved Element. Step 3
searches the declared R1 orientation (`plus`: R1 forward; `minus`: R1 reverse)
and the opposite R2 orientation; it never aligns both strands and filters
afterwards.

- Each full clipped query aligns to a substring of the Element with both
  terminal query bases on reference bases. Terminal gaps, soft clipping,
  skipped reference, and padding are not produced.
- Every substituted, inserted, or deleted base costs one edit, with no
  affine-gap surcharge. Any aligned `N` (in read or reference, including `N`
  against `N`) costs one edit.
- The pair's combined edits must be at most `--max-pair-edits`.
- Candidate placements are paired before ranking, so an individually
  non-best mate placement can belong to the best pair. Mate endpoints must
  satisfy Step 4's strict pair geometry.
- Equivalent minimum-edit paths over the same mate spans collapse to one
  deterministic CIGAR. Two or more distinct best span pairs are rejected as
  ambiguous.

Each rejected pair has exactly one reason: `unknown_barcode`,
`disagreeing_lookup_identities`, `no_acceptable_placement`,
`invalid_paired_geometry`, or `tied_best_distinct_placements`. Rejected pairs
do not enter the main BAM.

### Outputs

```text
LIB01_step3_alignment.bam
LIB01_step3_alignment.bam.bai
LIB01_step3_rejected_R1.fq.gz
LIB01_step3_rejected_R2.fq.gz
LIB01_step3_rejections.tsv.gz
LIB01_step3_summary.json
```

The coordinate-sorted BAM contains accepted pairs only: mapped primary mates
with standard pair flags, mate coordinates, reference-span TLEN, MAPQ 255, the
original UMI-bearing read name, read group `--library-prefix`, `NH:i:1`,
`HI:i:1`, per-mate `NM` equal to its edit count, `AS` equal to the negative
edit count, the canonical capture JSON in `xc:Z`, and the resolved Element in
`xe:Z`. The standard reference name and coordinates are authoritative; the
custom tags are for metadata inspection and are not required by Step 4.

Rejected FASTQs preserve the annotated, clipped input pairs. Zero accepted
pairs is a failure: no BAM or BAI is published, but rejection artifacts and a
failed summary with complete diagnostics are written. A midstream failure
retains closed evidence and marks diagnostics `incomplete`. Configuration
failures before read processing write no summary. All six output paths must
be absent before processing; a per-prefix lock serializes invocations.

### Resources

`--threads N` runs ordered batches of 64 pairs with up to `N` worker threads;
output order and scientific results do not depend on `N`. `samtools sort`
receives `N` sorting threads in total (`-@ N-1`) and
`--bam-sort-memory / N` per thread; other samtools commands use one thread.
The reference and barcode map are held in memory and scale with their size,
and each pair's candidate search covers all in-ceiling placements on its
selected Element, so total process memory is not constant. See [resource guidance](../cap-selection/resource-guidance.md).

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
| `--threads` | `16` | Positive integer CPU budget for pair workers, samtools and endpoint tools |
| `--max-pair-edits` | `4` | Non-negative integer; **inclusive** combined `NM(R1) + NM(R2)` base-edit ceiling |
| `--samtools` | `samtools` | samtools executable path or name |
| `--bedtools` | `bedtools` | BEDTools executable path or name |
| `--umi-dedup-method` | `directional` | UMI-tools `dedup --method` (`unique`, `percentile`, `cluster`, `adjacency`, `directional`) |
| `--umi-tools` | `umi_tools` | UMI-tools executable path or name |
| `--rna-strand` | `both` | Expected reference-relative biological RNA strand (`both`, `plus`, `minus`); also selects the published track set |

The former `--max-pair-mismatches` option is removed and is rejected as an
unrecognized argument (exit `2`). There is no reference path, BAI input,
project root, overwrite flag, batch mode, no-deduplication mode, or generic
passthrough to native tool CLIs. Native samtools, BEDTools, and UMI-tools
streams are captured internally, not exposed as the user interface.

Step 4 reads samtools output through a disk-backed temporary stream and batches
complete query-name groups for eligibility checks, using at most `--threads - 1`
worker processes while the parent coordinates and reduces their results.
`samtools -@` receives at most `--threads - 1` additional threads,
because samtools also has its main thread. Independent selected-strand BEDTools
endpoint calls may run concurrently, with at most `--threads - 1` tools active.
The global eligible-molecule UMI-tools deduplication, endpoint normalization,
track validation, summary reduction and publication remain serial. The summary's
additive `resources` object records requested threads, effective workers and
serial phases.

### BAM-only compatibility boundary

Step 4 admits structurally compatible **BAM** evidence only:

- Regular, readable, non-empty file; `samtools quick-check` succeeds
- Header `SO:coordinate`; records coordinate-ordered per `@SQ` order
- Unique `@SQ` names with positive lengths; order preserved in outputs
- Exactly one `@RG` with `ID` equal to `--library-prefix`
- Every alignment record has `RG` matching that ID

No BAI, external reference FASTA, or chromosome-size file is required. Step 3
provenance, the `xc:Z`/`xe:Z` tags, the barcode map, and the layout are not
required when an external BAM satisfies the rules above.

Every query name must end with the canonical fastp-produced UMI suffix:
`:UMI_` followed by exactly twelve uppercase `A`, `C`, `G`, or `T` bases
on both mates (the first whitespace-delimited identifier carries the
suffix). Missing, malformed (including the former `_UMI:` spelling), or
`N`-bearing UMI evidence fails the invocation before pair filtering, UMI-tools
deduplication, or track publication; there is no mode that skips UMI
deduplication. `N`-bearing UMIs produced by fastp are normally excluded
upstream by Step 1; a BAM that still contains them fails here.

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
| 4 | `cigar` | CIGAR must be full-query `M`, `=`, `X` with optional internal `I`/`D`, both query ends on reference bases, within the `@SQ` length, and with `NM` consistent with the CIGAR; clipping, terminal gaps, skips, and padding are rejected |
| 5 | `edit_ceiling` | `NM(R1) + NM(R2) > --max-pair-edits` (equality retains the pair) |
| 6 | `geometry` | Same reference; opposite strands; R1/R2 5′ positions ordered consistently with R2 as RNA 5′ and R1 as RNA 3′ |

Each eligible pair contributes one R2 **cap signal** observation (sequenced 5′
of R2) and one R1 **polymerase-position proxy** observation (sequenced 5′ of
R1, assigned directly to the R1 BAM strand). For a reverse-strand read, the
5′ position is computed from the CIGAR reference span: deletions extend it and
insertions do not. **R2 3′ endpoints are not consumed.**

**RNA strand assertion:** `--rna-strand` declares the expected
reference-relative biological RNA strand, determined by R1's BAM strand. It
is an assertion, not a filter: with `plus` or `minus`, any otherwise
eligible pair whose R1 lies on the opposite strand fails the invocation
before UMI-tools deduplication with its contradictory-pair count, and no
tracks are published. Pairs rejected by ordinary filters never count as
contradictory. Pass the same `--rna-strand` value used at Step 3; passing
`both` for a single-strand Step 3 BAM publishes two extra empty tracks.
Complete unmapped primary pairs without mapped-placement tags are admitted
and audited as ordinary unmapped (`excluded_flags`) pairs.

Eligible pairs are written to a staging BAM and deduplicated with UMI-tools
`dedup --paired` using `--umi-dedup-method` (default `directional`). Track
counts use **retained** pairs after deduplication.

BEDTools may merge adjacent endpoint positions with equal counts into a
single interval. Step 4 validates these intervals and expands them into
one-base evidence before writing tracks. Counts remain unchanged at each
position: a two-base interval with count three represents six observations,
two occupied positions, and maximum absolute pileup three. Plus-track values
are positive and minus-track values are negative.

**Zero eligible pairs** after filtering or **zero retained pairs** after UMI
deduplication is a failed invocation (`status: failed` in
`{prefix}.step4_summary.json` when written). Success and failure summaries
publish reconciled `pair_total_groups`, `eligible_pairs`,
`pre_dedup_eligible_pairs`, `umi_duplicate_pairs_removed`, `rejected_pairs`,
`rejection_counts`, and `edit_histogram` when pair auditing completed,
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

Encoding details: [cap-selection Step 4 bigWig tracks](../cap-selection/formats.md#step-4-endpoint-bigwigs)
and [Step 4 summary](../cap-selection/formats.md#step-4-summary-json-and-qc-fields).

### Concurrent runs and collisions

Step 4 acquires `.{prefix}_step4.lock` in the output directory for the
invocation. Only the selected track paths plus the summary must be absent
before processing (five paths for `both`, three for `plus`/`minus`);
existing outputs for omitted strands are unrelated files and are neither
checked nor removed. A cooperating second
invocation with the same prefix and directory receives an already-active error.

### Complete runnable example

After [Step 3](../cap-selection/steps-1-3.md#step-3-barcode-directed-alignment)
produced `aligned/LIB01_step3_alignment.bam` with `--rna-strand plus`:

```bash
cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix LIB01 \
  --input-bam aligned/LIB01_step3_alignment.bam \
  --output-dir tracks/ \
  --rna-strand plus \
  --threads 16 \
  --max-pair-edits 4 \
  --samtools samtools \
  --bedtools bedtools
```

Expect exit code `0`, no stdout, three new files under `tracks/`
(`LIB01.5pl.bw`, `LIB01.3pl.bw`, `LIB01.step4_summary.json`), and a summary
with `"status": "success"` in which `track_observations.cap_plus` and
`track_observations.proxy_plus` each equal `eligible_pairs` (mirrored for
`minus`; under `both`, the plus and minus totals of each endpoint type sum to
`eligible_pairs`).

### Help

```bash
cap-assay-pipeline step4-post-alignment-processing --help
```

Help prints on stdout with exit `0` without validating paths, resolving tools,
or running external commands. It documents the flags above, BAM admission,
tool minimums, endpoint meanings, track filenames, zero-eligible failure, and
an example invocation.
