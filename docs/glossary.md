# Canonical glossary

These definitions apply to the released **0.2.0b5** documentation and its
artifact and command names.

Use these definitions when reading pipeline commands, artifacts, summaries,
and troubleshooting guidance. Parenthetical aliases are deliberate search
terms, not synonyms for a different concept.

## Assay concepts

### Tested element (tested sequence)

A DNA sequence whose regulatory activity the assay evaluates.

### Element (Element identifier)

The identifier assigned to one tested-library sequence record. Opposite
orientations of the same physical tested element can have different Element
values. An Element value is therefore a record identifier, not a reliable
orientation-pair key.

### eBC branch (enhancer barcode branch)

The assay branch that measures enhancer activity. It uses the EID identifier
domain and produces an `EID-ActivityByElement` table.

### pBC branch (promoter barcode branch)

The assay branch that measures promoter activity. It uses the PID identifier
domain and produces a `PID-ActivityByElement` table.

eBC and pBC are assay branches. They are not alternate spellings of EID and
PID, which are identifier domains.

### CW (clockwise; forward orientation)

The clockwise orientation of a tested element in the construct. CW corresponds
to the forward reference orientation.

### CCW (counter-clockwise; reverse orientation)

The counter-clockwise orientation of a tested element in the construct. CCW
corresponds to the reverse reference orientation.

CW and CCW describe construct orientation, not assay branch or identifier
domain.

## Libraries and identifiers

### PreTran library (pre-transfection library)

A sequencing library collected before transfection. It establishes
associations between identifier observations and tested elements.

### PostTran library (post-transfection library)

A sequencing library collected after transfection. PostTran DNA and RNA
libraries quantify barcode abundance used for activity calling.

### DNA replicate and RNA replicate

A replicate sequencing library measuring the DNA-side or RNA-side abundance,
respectively. Step 9 aligns DNA and RNA replicate lists by index and requires
equal list lengths.

### UMI (unique molecular identifier)

A molecular tag used to deduplicate observations and count distinct molecules.
UMI counts are intermediate evidence; they are not themselves activity calls.

### EID (enhancer identifier)

The identifier domain used by the eBC branch. An EID is typically a 20-base-
pair random DNA barcode positioned so that it is co-transcribed with its
associated target gene. Its RNA abundance relative to its DNA abundance
reports enhancer activity. PreTran evidence associates EID values with tested
elements.

### PID (promoter identifier)

The identifier domain used by the pBC branch. A PID is typically a 20-base-
pair random DNA barcode positioned downstream of a tested element so that it
is co-transcribed with that element. Its RNA abundance relative to its DNA
abundance reports promoter activity. PreTran evidence associates PID values
with tested elements.

## Mapping and references

### Observed identifier (ObservedID)

An identifier sequence observed in sequencing data. It may be a noisy or
non-canonical form that must be resolved before downstream counting.

### Canonical identifier (CanonicalID)

The retained representative identifier to which an observed identifier is
resolved. Canonical IDs are used to make identifier counts consistent across
PostTran records.

### Cluster reference (identifier cluster reference)

A table mapping `ObservedID` to `CanonicalID` and its associated `Element`.
Cluster references are produced separately for each declared identifier
domain, such as EID and PID. The appropriate branch's reference is required
for PostTran matching and element mapping.

### Positional reference pairing (opposite-orientation pairing)

The CW/forward and CCW/reverse reference records at the same position in two
FASTA files represent opposite orientations of one physical tested element.
Pairing uses record position and not Element names or FASTA header text.

### Layout schema (layout-schema JSON)

A per-sample JSON description of the fields captured from paired reads and the
column order emitted by Step 2. It defines the `delimited-records` header for
that sample.

### Negative control (negative-control list)

An element identifier designated as a control for Step 9 baseline
normalization. Eligible controls must pass the same DNA representation rule
as candidates; a controls-only retained set fails. Before PostTran data
exists, `pretrans_nc_representation`
compares retained controls with other retained elements in the Step 5
`crosswalk-map` using the same annotation list and exact `Element` matching.

## Outputs and measurements

### MoleculeCount

The deduplicated molecule count for an identifier or element in a replicate
artifact. Step 8 emits element-level counts for Step 9.

### ActivityScore

The mean replicate-level log2 RNA-to-DNA ratio after applying the configured
pseudocount.

### ActivityZ

The negative-control-normalized z-score derived from the retained controls.

### ActivityCall

The deterministic output category for an element. In **0.2.0b5** it is
`Active`, `Repressive`, `NoCall`, or `Control`, assigned from the
control-relative effect and adjusted p-value. Historical **0.1.0b4** used
`Active` or `Inactive` from `ActivityZ` and `--activity-threshold-z`. It is
an output classification, not a claim that the assay has established a
biological mechanism.

## Cap-selection

Terms below apply to `cap-assay-pipeline` and cap-selection artifacts only.
They do not redefine reporter-assay Step numbers or PreTran/PostTran tables.

### Cap-selection assay

An assay that sequences cap-selected nascent RNA from construct libraries
before reporter-style barcode matching. QUASARR-cap is one cap-selection assay;
it shares plasmid construct context with QUASARR-seq but uses a different
pipeline command namespace and deliverables.

### Cap signal

The canonical name for observations derived from the **R2** sequenced 5′
endpoint (nascent RNA 5′). Published in `{prefix}.5pl.bw` and `{prefix}.5mn.bw`.

### Polymerase-position proxy

Observations derived from the **R1** sequenced 5′ endpoint, assigned directly
to the R1 BAM strand. Proxy coordinates retain their existing convention. Interprets a pause-biased nascent RNA 3′
endpoint; it is **not** cap signal and not unbiased Pol II occupancy. Published
in `{prefix}.3pl.bw` and `{prefix}.3mn.bw`.

### CAP layout

The version 1 JSON document passed to Step 2 `--layout`. It lists, for each
mate, ordered `fixed` anchors, named `capture` segments, and `sequence`
segments, and marks one contiguous retained interval. It is distinct from the
reporter-assay layout schema.

### Capture

A named read segment extracted by Step 2, optionally reverse-complement
normalized. Capture names are arbitrary; no name, including `PID`, has
built-in meaning. All captures travel in the read names as a `CAP1`
annotation and in Step 3 BAM tag `xc:Z`.

### CAP1 annotation

The `|CAP1=<payload>` marker Step 2 adds to each mate's first name token,
immediately before the `:UMI_` suffix. The payload is unpadded URL-safe base64
of canonical JSON mapping capture names to normalized values.

### Barcode field

A capture selected with Step 3 `--barcode-field NAME` (repeatable). Only
selected fields are looked up in the barcode map; every selected field must
resolve to the same Element. Unselected captures are metadata.

### Barcode map

The CAP-owned UTF-8 TSV passed to Step 3 `--barcode-map`, with `barcode` and
`Element` columns. Lookup is exact. Several barcodes may identify one Element;
one barcode cannot identify two.

### Element-only reference

The Step 3 FASTA of tested-element sequences, without identity barcodes or
construct flanks, keyed by Element ID. BAM and track coordinates are positions
within these records, not genomic or construct coordinates. Identical
sequences may appear under different Element IDs. It replaces the
construct-derived reference used by releases before 0.2.0b5.

### Pair edits

The combined number of substituted, inserted, and deleted bases across both
mates of a pair (`NM(R1) + NM(R2)`), compared inclusively with
`--max-pair-edits` (default 4) at Steps 3 and 4.

### Library prefix

The filename-safe token shared across cap-selection steps. Step 3 writes it as
the BAM read-group ID, and Step 4 requires the sole BAM read-group ID to match
`--library-prefix`.

### Reference-relative RNA strand

The plus or minus biological RNA strand measured relative to an element-only
reference record, independent of the tested element's CW or CCW orientation.
Determined by the R1 BAM strand: forward means plus; reverse means minus.
Step 3 requires `--rna-strand plus` or `minus` and searches only that strand.
Step 4 accepts `--rna-strand {both,plus,minus}` (default `both`); callers
repeat the Step 3 value because the BAM carries no policy marker.
