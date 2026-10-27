# Cap-selection Steps 1–3

This page documents the released **0.2.0b5** handoffs for the cap-selection
steps that feed [Step 4](workflow.md#step-4-deliverable). All three steps are
required. Full flag lists live in `cap-assay-pipeline <step> --help` and the
[Cap-selection CLI](../cli/cap-assay.md).

## Step 1: Prepare FASTQ

```bash
cap-assay-pipeline step1-prep-fastq \
  --library-prefix LIB01 \
  --input-r1 raw_LIB01_R1.fastq.gz \
  --input-r2 raw_LIB01_R2.fastq.gz \
  --output-dir prepared/
```

`fastp` trims adapters, moves a 12-base R1 UMI into read names, and applies
ordinary paired read filtering. Step 1 then excludes both mates of every
pair whose extracted 12-base UMI contains an ambiguous (`N`) base: published
FASTQs contain only synchronized pairs with twelve `A`/`C`/`G`/`T` UMI
bases, and the step summary reports the excluded count separately as
`ambiguous_umi_pairs_removed` alongside `fastp_output_read_pairs` (pairs
fastp retained before exclusion). A missing or malformed UMI annotation, or
zero remaining pairs, fails the invocation instead of publishing. Step 1
does not remove PCR duplicates by sequence or UMI; UMI-aware molecule
deduplication runs in Step 4.

Step 1 `--threads` is a positive CPU budget (default 16). Its gzip traversal
and ordered publication run in the parent, with at most `threads - 1` Python
worker processes; `--threads 1` runs directly. Validation and UMI exclusion
use bounded paired chunks, so record buffering does not grow with library size.
Fastp runs in a separate phase with the selected worker budget and may use fixed
reader/writer threads in addition. The summary's additive `resources` object
records configured workers, observed worker PIDs, chunk bounds and fastp threads.
Scientific counts and paired record order remain equivalent across budgets.

Step 1 publishes `LIB01_R1.trim.fq.gz`, `LIB01_R2.trim.fq.gz`, and
`LIB01_step1_summary.json`; consult the summary for exact paths and fastp
filtering metrics. Step 1 behavior is unchanged from earlier releases.

## Step 2: Identify and clip

```bash
cap-assay-pipeline step2-identify-and-clip \
  --library-prefix LIB01 \
  --input-r1 prepared/LIB01_R1.trim.fq.gz \
  --input-r2 prepared/LIB01_R2.trim.fq.gz \
  --layout cap-layout.json \
  --output-dir identified/
```

Step 2 is mandatory. It matches the [layout JSON](formats.md#step-2-layout-json-schema-version-1)
at fixed positions in each prepared pair, extracts and normalizes the named
captures, and keeps one contiguous interval of each mate. A pair is retained
only when exactly one layout matches, every fixed anchor is within its
substitution tolerance (`--max-anchor-mismatches`, default 1 per anchor),
every capture fits its alphabet, repeated captures agree, and each retained
mate has at least `--min-retained-length` bases (default 15).

Retained pairs are written to `LIB01_R1.ident.fq.gz` and
`LIB01_R2.ident.fq.gz`. Both mates carry the captures in a `CAP1`
annotation placed immediately before the unchanged `:UMI_` suffix; see
[CAP1 annotation](formats.md#cap1-read-name-annotation). Rejected pairs are
written unchanged to `LIB01_step2_rejected_R1.fq.gz` and
`LIB01_step2_rejected_R2.fq.gz`, with one reason per pair in
`LIB01_step2_rejections.tsv.gz`.

Check `LIB01_step2_summary.json` (schema `2.0`) before continuing:
`status: "success"`, `complete: true`, and `pair_count_reconciled: true`.
`rejection_reasons` shows why pairs were rejected; a high
`anchor_or_length_mismatch` count usually means the layout does not describe
the reads. Zero retained pairs fails the step, but the rejection files and a
failed summary are still written for diagnosis.

`--threads` is a positive CPU budget, default 1: the parent performs gzip
traversal, ordered output and publication while up to `threads - 1` worker
processes evaluate bounded chunks. Output gzip compression defaults to level 1;
choose 0 (fastest, largest) through 9 (slowest, smallest) with
`--gzip-compression-level`.

## Step 3: Barcode-directed alignment

```bash
cap-assay-pipeline step3-alignment \
  --library-prefix LIB01 \
  --input-r1 identified/LIB01_R1.ident.fq.gz \
  --input-r2 identified/LIB01_R2.ident.fq.gz \
  --reference elements.fa \
  --barcode-map barcodes.tsv \
  --barcode-field identity_5 \
  --barcode-field identity_3 \
  --rna-strand plus \
  --output-dir aligned/
```

Step 3 first validates the complete [element-only FASTA](formats.md#step-3-element-only-reference-fasta)
and [barcode map](formats.md#step-3-barcode-map-tsv). For each pair it reads
the captures named by `--barcode-field` from the `CAP1` annotation, looks
each value up exactly in the barcode map, and requires all selected fields to
resolve to the same Element. Other captures are carried only as metadata.
Pairs with an unknown barcode or disagreeing identities are rejected before
alignment.

Each remaining pair is aligned natively to its Element's sequence only.
Step 3 searches the R1 orientation given by `--rna-strand` (`plus`: forward;
`minus`: reverse) and the opposite R2 orientation. Full clipped reads must
align end to end within the Element; substitutions, insertions, and deletions
each cost one edit per base, and the pair total must not exceed
`--max-pair-edits` (default 4). Mates are ranked jointly under Step 4's pair
geometry. A pair with no in-ceiling placement, only invalid geometry, or two or
more distinct best placements is rejected.

Successful publication includes:

```text
LIB01_step3_alignment.bam
LIB01_step3_alignment.bam.bai
LIB01_step3_rejected_R1.fq.gz
LIB01_step3_rejected_R2.fq.gz
LIB01_step3_rejections.tsv.gz
LIB01_step3_summary.json
```

The BAM holds accepted pairs only, in element coordinates, with the captures
in `xc:Z` and the resolved Element in `xe:Z`. Verify in the summary (schema
`4.0`) that `status` is `success`, `counts.accepted_plus_rejected_reconciled`
is `true`, and `diagnostics_status` is `complete`. `counts.reasons` breaks
rejections down by reason. Zero accepted pairs is a Step 3 failure: no BAM is
published, but the rejection files and failed summary remain.

`--threads` is a positive CPU budget (default 16) for ordered pair batches and
`samtools sort`. `--bam-sort-memory` (default `2G`, divided across sorting
threads) and `--tmp-dir` control sorting; see [resource
guidance](resource-guidance.md).

## Resume at Step 4

Pass the same `--rna-strand` value used at Step 3 (see [RNA strand
policy](workflow.md#rna-strand-policy)). When a compatible BAM already exists:

```bash
cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix LIB01 \
  --input-bam aligned/LIB01_step3_alignment.bam \
  --rna-strand plus \
  --output-dir tracks/
```

See [Generate endpoint tracks](step4.md) and [Cap-selection CLI — Step
4](../cli/cap-assay.md#step4-post-alignment-processing) for BAM admission,
pair filtering, and tool requirements.
