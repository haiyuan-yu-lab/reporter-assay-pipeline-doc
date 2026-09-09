# Canonical glossary

These definitions apply to the released **0.1.0b3** documentation and its
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
normalization. Controls must remain in the shared retained analysis space for
the invocation to succeed. Before PostTran data exists, `pretrans_nc_representation`
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

The deterministic `Active` or `Inactive` category assigned from `ActivityZ`
and the configured activity threshold. It is an output classification, not a
claim that the assay has established a biological mechanism.
