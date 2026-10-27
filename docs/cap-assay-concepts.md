# Cap assay concepts

The cap-selection assay measures nascent RNA endpoints from cap-selected
cDNA. It produces endpoint tracks in the coordinates of each tested element;
it does not produce reporter activity tables.

## Barcode-directed element identity

Each read pair carries identity barcodes from the library design. Step 2 uses
a CAP layout to extract named captures from fixed read positions and records
them in the read names. Step 3 looks up the captures you select with
`--barcode-field` in a barcode→Element map and aligns the pair only to that
Element's sequence. Identity comes from the barcode, not from searching the
whole reference, so differently barcoded Elements may share an identical
sequence. Lookup is exact: a barcode that is not in the map, or selected
fields that disagree, reject the pair.

## Element-only coordinates

The alignment reference contains tested-element sequences alone, without
identity barcodes or construct flanks. BAM and track coordinates are
therefore positions within the tested element. Tracks from releases before
0.2.0b5, which aligned to construct-derived references with flank offsets,
are not directly comparable; see [Migrating to
0.2.0b5](cap-selection/migrating-to-0.2.0b5.md).

## Edits

Step 3 aligns each full clipped read end to end within the Element. Each
substituted, inserted, or deleted base counts as one edit, and the two mates'
edits are summed and compared with `--max-pair-edits` (default 4) at Steps 3
and 4. Internal insertions and deletions are allowed; clipping and terminal
gaps are not.

## Reference-relative RNA strand

Plus and minus refer to the biological RNA strand relative to the
element-only reference record. R1 determines that strand: a forward R1
alignment means plus, and a reverse alignment means minus. This strand is
independent of the tested element's CW or CCW orientation. Step 3 searches
one declared strand, so each invocation needs the library's known strand. The
[cap workflow](cap-selection/workflow.md#rna-strand-policy) explains the
operational strand policy.

## Two endpoint measurements

| Measurement | Read source | Biological interpretation |
| --- | --- | --- |
| Cap signal | R2 sequenced 5′ endpoint | Observation of nascent RNA initiation / capped 5′ endpoint |
| Polymerase-position proxy | R1 sequenced 5′ endpoint, assigned to the R1 strand | Pause-biased proxy for the nascent RNA 3′ endpoint |

Step 4 publishes cap signal as `.5pl.bw` / `.5mn.bw` and the polymerase-position
proxy as `.3pl.bw` / `.3mn.bw`. The proxy is not cap signal and is not an
unbiased measure of RNA polymerase II occupancy. Coordinates and signs are
defined by the released [format contract](cap-selection/formats.md#step-4-endpoint-bigwigs).

For commands and input requirements, see [Prepare inputs and reference](cap-selection/prepare-inputs.md)
and the [cap workflow](cap-selection/workflow.md).
