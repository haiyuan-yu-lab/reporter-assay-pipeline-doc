# Complete cap assay run example

This example connects read preparation, an external reference, alignment, and
endpoint generation for one library, `LIB01`. Replace the example paths with
your files. The detailed contracts for each stage are in [Steps 1–3](steps-1-3.md)
and the [cap CLI reference](../cli/cap-assay.md).

First prepare the complete construct reference as described in [Prepare inputs
and reference](prepare-inputs.md):

```bash
ExogenousSequenceTools assemble add_adapter \
  --fasta tested_elements.fasta \
  --left_adapter_fasta left_adapter.fasta \
  --right_adapter_fasta right_adapter.fasta \
  --output_fasta reference/CONSTRUCT01_reference.fasta
```

Prepare the paired reads:

```bash
cap-assay-pipeline step1-prep-fastq \
  --library-prefix LIB01 \
  --input-r1 raw_LIB01_R1.fastq.gz \
  --input-r2 raw_LIB01_R2.fastq.gz \
  --output-dir prepared/
```

If the prepared reads require construct-flank clipping, run optional Step 2 and
use its outputs in Step 3. Otherwise, use the Step 1 outputs directly:

```bash
cap-assay-pipeline step2-clip-construct-flank \
  --library-prefix LIB01 \
  --input-r1 prepared/LIB01_R1.trim.fq.gz \
  --input-r2 prepared/LIB01_R2.trim.fq.gz \
  --clip-layout construct_flank.json \
  --output-dir clipped/
```

Align the selected FASTQ pair. Set `--rna-strand` to the selected policy and
use the same value for Step 4; `both` is shown here:

```bash
cap-assay-pipeline step3-alignment \
  --library-prefix LIB01 \
  --input-r1 clipped/LIB01_R1.clip.fq.gz \
  --input-r2 clipped/LIB01_R2.clip.fq.gz \
  --reference reference/CONSTRUCT01_reference.fasta \
  --rna-strand both \
  --output-dir aligned/
```

When clipping does not apply, replace the two `clipped/` paths with the Step 1
trim FASTQ paths. Then generate the strand-selected endpoint tracks from the
successful Step 3 BAM:

```bash
cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix LIB01 \
  --input-bam aligned/LIB01_step3_alignment.bam \
  --rna-strand both \
  --output-dir tracks/
```

Confirm each step summary reports success before continuing. Step 4 writes
cap-signal tracks and polymerase-position proxy tracks; see [Cap assay
concepts](../cap-assay-concepts.md#two-endpoint-measurements) and [format
contracts](../formats.md#cap-selection-step-4-bigwig-tracks) for their meaning.
