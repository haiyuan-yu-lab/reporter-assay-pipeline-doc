# Migrate CAP reference assembly and optional clipping

Starting with **0.2.0b3**, the CAP interface prepares references outside the numbered workflow
and names optional clipping Step 2. Replace the former
`step2-build-reference` builder with the external assembly command below. Rename
`step1b-clip-construct-flank` to `step2-clip-construct-flank`; its arguments and
clipped FASTQ names stay the same, while `<prefix>_step1b_summary.json` becomes
`<prefix>_step2_summary.json`. Step 3 and Step 4 retain their command names and
numbering. When clipping does not apply, pass compatible Step 1 FASTQs directly
to Step 3 without creating a clipping summary.

Replace the old builder invocation with
`ExogenousSequenceTools assemble add_adapter`. If the former
`construct_layout.json` contained a `left_fixed` region and a `right_fixed`
region, copy each region's `sequence` value into its own one-record adapter
FASTA. The `tested_element` region maps to the tested-element FASTA:

```json
{
  "regions": [
    {"type": "left_fixed", "sequence": "ACGT"},
    {"type": "tested_element"},
    {"type": "right_fixed", "sequence": "TGCA"}
  ]
}
```

Create the adapter files with the complete sequence strings from the former
layout:

```text
>left_adapter
ACGT
```

```text
>right_adapter
TGCA
```

Then assemble the complete reference:

```bash
ExogenousSequenceTools assemble add_adapter \
  --fasta tested_elements.fasta \
  --left_adapter_fasta left_adapter.fasta \
  --right_adapter_fasta right_adapter.fasta \
  --output_fasta reference/CONSTRUCT01_reference.fasta
```

Each adapter FASTA must contain exactly one record. The right adapter is
optional when the construct has no fixed right region. Output records contain
`left + tested element + right`, and each tested-element FASTA identifier is
preserved. CAP consumes only this ordinary FASTA. Step 3 does not need builder
annotations, a manifest, an assembly summary, XP provenance, or an XP
installation. It rejects identical complete sequences across distinct IDs
before STAR runs.

This external command runs during reference preparation. CAP's Step 3 alignment
can run in an environment without XP genomic tools. Continue to use compatible
prepared FASTQs directly with Step 3 when clipping does not apply.

The old clipping invocation remains valid after changing only its command
name:

```bash
cap-assay-pipeline step2-clip-construct-flank \
  --library-prefix LIB01 \
  --input-r1 prepared/LIB01_R1.trim.fq.gz \
  --input-r2 prepared/LIB01_R2.trim.fq.gz \
  --clip-layout construct_flank.json \
  --output-dir clipped/
```

The former `step1b-clip-construct-flank` spelling has no compatibility alias.
