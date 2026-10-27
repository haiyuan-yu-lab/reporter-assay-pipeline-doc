# Prepare cap assay inputs and reference

The released **0.2.0b5** cap workflow needs four operator-prepared inputs per
library design. CAP does not build references, infer barcode assignments, or
read barcode-adder metadata.

| Input | Used by | Format |
| --- | --- | --- |
| Raw paired FASTQs | Step 1 | R1 begins with a 12-base A/C/G/T UMI, followed by the configured R1 layout; R2 follows the configured R2 layout. Mates share logical read names. |
| CAP layout JSON | Step 2 `--layout` | [Schema version 1](formats.md#step-2-layout-json-schema-version-1) |
| Barcode map TSV | Step 3 `--barcode-map` | [`barcode` and `Element` columns](formats.md#step-3-barcode-map-tsv) |
| Element-only FASTA | Step 3 `--reference` | [Tested-element sequences only](formats.md#step-3-element-only-reference-fasta) |

## Describe the read layout

Write one layout for each read structure in the library. For each mate, list
the segments in sequencing order (after Step 1 has removed the R1 UMI):

- `fixed` segments for construct anchors that must match at that position;
- `capture` segments for the fields you want to record, such as element
  barcodes or other identifiers, each with a name you choose;
- `sequence` segments for the remaining bases, usually one `"rest"` segment
  holding the element-derived payload.

Mark the bases to keep for alignment with `"retain": true`; they must be one
contiguous interval per mate, and normally contain only tested-element
sequence. Use `"normalize": "reverse_complement"` for a capture that is read in
the opposite orientation so that both observations of the same barcode share
one value. A complete example is in [Migrating to
0.2.0b5](migrating-to-0.2.0b5.md#layout-json).

## Write the barcode map

List every identity barcode and the Element it identifies, using the
canonical (normalized) barcode value as Step 2 records it:

```text
barcode	Element
ACGCTA	Element_001
```

Decide which captures identify the Element; you will name them at Step 3 with
`--barcode-field`. When several fields are selected, they must all resolve to
the same Element. A barcode cannot identify two Elements, but one Element can
have several barcodes.

## Prepare the element-only reference

Supply an ordinary FASTA whose record IDs are the `Element` values and whose
sequences are the tested elements alone, without identity barcodes, adapters,
or construct flanks. Do not use a construct reference assembled with
`ExogenousSequenceTools assemble add_adapter` from earlier releases: its
flank coordinates and sequences no longer apply. Records with identical
sequences are allowed when different barcodes identify them.

## Prepare reads and choose the strand

Run `step1-prep-fastq`, then `step2-identify-and-clip` on its outputs, then
pass the Step 2 `.ident.fq.gz` files to Step 3. Choose the library's
reference-relative RNA strand before alignment and give the same
`--rna-strand plus` or `--rna-strand minus` to Steps 3 and 4. See [Prepare
and align reads (Steps 1–3)](steps-1-3.md) for command handoffs, paths, and
summaries.
