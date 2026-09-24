# Cap-selection Steps 1–3

This page documents released **0.2.0b1** handoffs for the cap-selection legs
that feed [Step 4](workflow.md#step-4-deliverable). Full flag lists live in
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
ordinary paired read filtering. Step 1 does not remove PCR duplicates by
sequence or UMI; UMI-aware molecule deduplication runs in Step 4. Each step
is independently runnable: prepared FASTQ from any compatible source is valid
for Step 3 when it satisfies Step 3’s FASTQ contract (including externally
prepared reads without Step 1 provenance).

Typical published artifacts under `--output-dir` use the library prefix in
their names; consult Step 1 help and `{prefix}_step1_summary.json` for the
exact paths, fastp filtering metrics, and the Step 4 deduplication handoff.

## Step 2: Construct-derived reference

```bash
cap-assay-pipeline step2-build-reference \
  --library-prefix CONSTRUCT01 \
  --construct-layout construct_layout.json \
  --output-dir reference/
```

Step 2 does not consume Step 1 output. The construct layout is a cap-selection
domain entity (not the reporter-assay layout schema). Each Element must yield a
unique normalized complete constructed sequence (left fixed, tested element, and
right fixed concatenated); duplicate complete sequences across distinct Elements
fail before any successful bundle is published. The standard FASTA emitted here
is the only required reference handoff for Step 3.

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
