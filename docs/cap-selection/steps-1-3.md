# Cap-selection Steps 1–3

This page documents the upcoming external-reference handoffs for the
cap-selection legs that feed [Step 4](workflow.md#step-4-deliverable). The
released **0.2.0b2** still has the former reference-builder command. Full flag lists live in
`cap-assay-pipeline <step> --help` and in the [Cap-selection CLI](../cli/cap-assay.md).

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
deduplication runs in Step 4. Each step is independently runnable: prepared
FASTQ from any compatible source is valid for Step 3 when it satisfies Step
3’s FASTQ contract (including externally prepared reads without Step 1
provenance).

Typical published artifacts under `--output-dir` use the library prefix in
their names; consult Step 1 help and `{prefix}_step1_summary.json` for the
exact paths, fastp filtering metrics, and the Step 4 deduplication handoff.

## Optional Step 1b: Construct-flank clipping

When a library’s prepared R1 reads begin with a known construct flank, run:

```bash
cap-assay-pipeline step1b-clip-construct-flank \
  --library-prefix LIB01 \
  --input-r1 prepared/LIB01_R1.trim.fq.gz \
  --input-r2 prepared/LIB01_R2.trim.fq.gz \
  --clip-layout construct_flank.json \
  --gzip-compression-level 1 \
  --output-dir clipped/
```

Use `{prefix}_R1.clip.fq.gz` and `{prefix}_R2.clip.fq.gz` as Step 3 inputs.
The JSON layout selects independent clip targets (for example R1 clipping for
both CW and CCW layouts while R2 3′ clipping applies only to CW). R2-only
configurations still match construct layout on R1 to recover the PID. When
clipping does not apply, **bypass** this step and point Step 3 at the Step
1 trim FASTQs directly. Step 3 does not require clip provenance for compatible
paired FASTQs. Step 1b validates and clips the paired streams in one pass,
then publishes its outputs after both inputs finish successfully. Output gzip
compression defaults to level 1 for faster processing; choose a level from 0
(fastest and largest) through 9 (smallest and slowest) with
`--gzip-compression-level`.

## External reference assembly (unnumbered prerequisite)

See the [migration guide](external-reference-migration.md) for converting the
former construct-layout fixed regions into adapter FASTAs.

```bash
ExogenousSequenceTools assemble add_adapter \
  --fasta tested_elements.fasta \
  --left_adapter_fasta left_adapter.fasta \
  --right_adapter_fasta right_adapter.fasta \
  --output_fasta reference/CONSTRUCT01_reference.fasta
```

This is a reference-preparation prerequisite outside the numbered CAP command
sequence. Each adapter FASTA contains exactly one record. The tool assembles
`left + tested element + right`, preserves each tested-element FASTA identifier,
and writes the complete reference sequences as ordinary FASTA. The right adapter
is optional when the construct has no fixed right region. A former CAP layout's
`left_fixed.sequence` and `right_fixed.sequence` values become the corresponding
one-record adapter FASTAs; the `tested_element` region maps to the input FASTA.
Step 3 accepts compatible external FASTA without XP provenance or builder
annotations, manifests, or summaries. It rejects uppercase-identical complete
sequences across distinct IDs before invoking STAR.

The current clipping command remains named Step 1b in this migration. This
change removes the former Step 2 builder and does not renumber clipping.

## Step 3: Alignment

```bash
cap-assay-pipeline step3-alignment \
  --library-prefix LIB01 \
  --input-r1 prepared/LIB01_R1.fastq.gz \
  --input-r2 prepared/LIB01_R2.fastq.gz \
  --reference reference/CONSTRUCT01.fasta \
  --output-dir aligned/
```

STAR aligns the library; samtools produces a coordinate-sorted BAM and index.
Step 3 also checks the complete FASTA before probing or invoking STAR. It
rejects two distinct first-token reference identifiers with identical
sequences after uppercasing literal sequence strings, for both generated and
supplied STAR indexes, and reports the colliding identifiers. Compatible
standalone FASTA needs no annotations, manifest, assembly summary, or XP
provenance. Reverse complements remain distinct unless their literal complete
strings match, and IUPAC symbols are compared literally without expansion.
The check compares complete records, not tested-element subsequences.
Successful publication includes:

```text
LIB01_step3_alignment.bam
LIB01_step3_alignment.bam.bai
LIB01_step3_summary.json
```

Verify `status` is `success` in the summary before Step 4. Zero uniquely mapped
pairs is a Step 3 failure; Step 4 also fails when no read pairs pass its filter.

### Step 3 RNA strand selection

Step 3 accepts `--rna-strand {both,plus,minus}` (default `both`). The value
names the reference-relative biological RNA strand determined by the R2 BAM
strand (R1 is the antisense mate); it never describes CW/CCW construct
orientation. The default publishes STAR's coordinate-sorted BAM unchanged.

With `plus` or `minus`, Step 3 keeps all and only tied-best placements whose
R2 lies on the selected strand, keeping linked R1/R2 mates together. One
surviving placement becomes unique (`NH:1`); several survivors stay
multimapped; no lower-scoring placement is ever substituted. A pair whose
best placements are all on the excluded strand is retained as one complete
unmapped pair and counted in `strand_rejected_pairs` (a subset of effective
unmapped pairs in `effective_mapping_counts`), with one warning reporting the
total rejected count. Partly or fully unmapped STAR pairs are preserved
unchanged and never count as strand-rejected.

## Resume at Step 4

Pass the same `--rna-strand` value used at Step 3 (see [RNA strand
policy](workflow.md#rna-strand-policy)).

When a compatible BAM already exists:

```bash
cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix LIB01 \
  --input-bam aligned/LIB01_step3_alignment.bam \
  --output-dir tracks/
```

See [Cap-selection CLI — Step 4](../cli/cap-assay.md#step4-post-alignment-processing)
for BAM admission, pair filtering, tool requirements, and the complete example.
