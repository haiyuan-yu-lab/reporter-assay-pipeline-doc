# Prepare cap assay inputs and reference

The released **0.2.0b4** cap workflow uses externally prepared references. It
does not include a numbered reference-builder command. Step 2 is optional
construct-flank clipping; when clipping does not apply, pass compatible Step 1
FASTQs directly to Step 3.

## Prepare the construct reference

Use the tested-element FASTA and the construct's fixed-flank sequences to
assemble a complete reference with `ExogenousSequenceTools assemble add_adapter`.
For each fixed region, create a one-record adapter FASTA containing its full
sequence. The right adapter is optional when the construct has no fixed right
region. For example:

```bash
ExogenousSequenceTools assemble add_adapter \
  --fasta tested_elements.fasta \
  --left_adapter_fasta left_adapter.fasta \
  --right_adapter_fasta right_adapter.fasta \
  --output_fasta reference/CONSTRUCT01_reference.fasta
```

The resulting reference records contain left adapter, tested element, and
right adapter, and preserve tested-element identifiers. CAP consumes this
ordinary FASTA; Step 3 does not need assembly annotations, manifests, or an
XP installation. The complete construct sequence must be distinct for each
Element ID.

## Prepare reads

Run `step1-prep-fastq` on paired cap-assay FASTQs. If construct-flank clipping
is required, run `step2-clip-construct-flank` on the Step 1 outputs and provide
its outputs to Step 3. Otherwise, provide Step 1 outputs directly to Step 3.
The optional clipping configuration describes the targeted flank sequence;
see the [cap CLI reference](../cli/cap-assay.md#step2-clip-construct-flank-optional).

Step 3 aligns prepared FASTQs to the complete construct-derived FASTA. Choose
the reference-relative RNA strand policy before alignment and use the same
`--rna-strand` selection in Steps 3 and 4. See [Prepare and align reads (Steps
1–3)](steps-1-3.md) for command handoffs, paths, and summaries.
