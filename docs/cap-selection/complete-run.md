# Complete cap assay run example

This example runs all four steps for one plus-strand library, `LIB01`.
Replace the example paths with your files. The detailed contracts for each
stage are in [Steps 1–3](steps-1-3.md), [Step 4](step4.md), and the [cap CLI
reference](../cli/cap-assay.md).

First prepare the inputs described in [Prepare inputs and
reference](prepare-inputs.md):

- `inputs/raw_R1.fastq.gz` and `inputs/raw_R2.fastq.gz` — raw paired reads;
- `inputs/cap-layout.json` — the CAP layout (schema version 1);
- `inputs/barcodes.tsv` — the barcode→Element map;
- `inputs/elements.fa` — the element-only reference.

Run each step in a fresh output directory and confirm each summary reports
success before continuing:

```bash
set -euo pipefail
LIB=LIB01
INPUTS=./inputs
OUT=./results/LIB01
mkdir -p "$OUT"

cap-assay-pipeline step1-prep-fastq \
  --library-prefix "$LIB" \
  --input-r1 "$INPUTS/raw_R1.fastq.gz" \
  --input-r2 "$INPUTS/raw_R2.fastq.gz" \
  --output-dir "$OUT/step1" \
  --threads 8

cap-assay-pipeline step2-identify-and-clip \
  --library-prefix "$LIB" \
  --input-r1 "$OUT/step1/${LIB}_R1.trim.fq.gz" \
  --input-r2 "$OUT/step1/${LIB}_R2.trim.fq.gz" \
  --layout "$INPUTS/cap-layout.json" \
  --output-dir "$OUT/step2" \
  --min-retained-length 15 \
  --max-anchor-mismatches 1 \
  --threads 4

cap-assay-pipeline step3-alignment \
  --library-prefix "$LIB" \
  --input-r1 "$OUT/step2/${LIB}_R1.ident.fq.gz" \
  --input-r2 "$OUT/step2/${LIB}_R2.ident.fq.gz" \
  --reference "$INPUTS/elements.fa" \
  --barcode-map "$INPUTS/barcodes.tsv" \
  --barcode-field identity_5 \
  --barcode-field identity_3 \
  --rna-strand plus \
  --max-pair-edits 4 \
  --threads 8 \
  --output-dir "$OUT/step3"

cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix "$LIB" \
  --input-bam "$OUT/step3/${LIB}_step3_alignment.bam" \
  --rna-strand plus \
  --max-pair-edits 4 \
  --threads 8 \
  --output-dir "$OUT/step4"
```

`identity_5` and `identity_3` are the capture names defined in this example's
layout; use the names from your own layout. For a minus-strand library, pass
`--rna-strand minus` to both Steps 3 and 4; Step 4 then publishes `.5mn.bw` and
`.3mn.bw`.

Step 4 writes cap-signal tracks and polymerase-position proxy tracks; see [Cap
assay concepts](../cap-assay-concepts.md#two-endpoint-measurements) and [format
contracts](formats.md#step-4-endpoint-bigwigs) for their meaning. If any step
fails, inspect its summary and rejection files as described in [Cap assay
troubleshooting](troubleshooting.md).
