# Migrating cap assay runs to 0.2.0b5

Release **0.2.0b5** is a breaking change to `cap-assay-pipeline`. It changes
how CAP identifies reads, chooses a reference, aligns pairs, and interprets
coordinates. Reporter assay commands and behavior are unchanged.

**Start a fresh run directory and regenerate every Step 2–4 output.** Do not
reuse STAR BAMs, STAR indexes, Step 2/3/4 summaries, cached derivations, or
endpoint tracks produced by **0.2.0b4** or earlier as though their meanings
were unchanged. Step 1 outputs keep their meaning, but the simplest safe
migration reruns Steps 1–4 in a new directory.

## What changed

The required workflow is now:

```text
raw paired FASTQ → Step 1 preparation → Step 2 named-field identification
→ Step 3 barcode-directed alignment → Step 4 endpoint tracks
```

- **Step 2 is mandatory.** `step2-clip-construct-flank` and its
  `--clip-layout` option are removed with no alias. The new command is
  `step2-identify-and-clip`, configured by a CAP-owned layout JSON passed with
  `--layout`. Step 1 FASTQs can no longer be passed directly to Step 3.
- **STAR is removed.** Step 3 no longer invokes STAR or builds or accepts STAR
  indexes. `--star`, `--star-index-dir`, `--max-multimaps`, and
  `--random-seed` are removed with no alias. STAR is not a dependency.
- **Step 3 is barcode-directed.** Step 3 reads named captures from the Step 2
  read names, looks up the fields you select with one or more
  `--barcode-field NAME` options in a barcode→Element TSV (`--barcode-map`),
  and aligns the pair only against that Element's sequence.
- **References are element-only.** The Step 3 FASTA contains tested-element
  sequences alone. Do not add identity barcodes or construct flanks, and do
  not use an `ExogenousSequenceTools assemble add_adapter` construct reference.
- **Step 3 requires one explicit RNA strand.** `--rna-strand` accepts only
  `plus` or `minus` and has no default; `both` is removed at Step 3. Give the
  same value to Step 4.
- **Native alignment tolerates indels.** Substitutions, insertions, and
  deletions each cost one edit per base, combined across both mates under
  `--max-pair-edits` (default 4).
- **Step 4 counts edits, not mismatches.** Step 4 `--max-pair-mismatches` is
  removed; use `--max-pair-edits`. Step 4 now accepts eligible alignments with
  internal insertions and deletions.
- **Summary schemas changed.** Step 2 summary schema is `2.0`, Step 3 schema is
  `4.0`, and Step 4 schema is `2.0`. Old mismatch-named Step 4 fields are not
  aliases.
- **New diagnostics.** Steps 2 and 3 each publish paired rejected-read FASTQs
  and a structured rejection table.

## New inputs

Prepare these local inputs before running:

| Input | Used by | Contents |
| --- | --- | --- |
| Raw paired FASTQs | Step 1 | R1 begins with a 12-base A/C/G/T UMI, then the configured R1 layout prefix and payload; R2 has its configured R2 prefix and payload. Mates have matching logical read names. |
| Layout JSON (`cap-layout.json`) | Step 2 `--layout` | Version 1 CAP layout describing fixed anchors, named captures, and retained read intervals for each mate. |
| Barcode map (`barcodes.tsv`) | Step 3 `--barcode-map` | UTF-8 TSV with `barcode` and `Element` columns. |
| Element FASTA (`elements.fa`) | Step 3 `--reference` | Tested-element sequences only, with Element IDs as unique first tokens. |

Step 1 extracts the first twelve R1 bases and appends the same
`:UMI_<12 A/C/G/T>` suffix to both prepared mates; Step 2 requires those
prepared suffixes to agree.

### Layout JSON

The layout document has integer `schema_version: 1` and a non-empty `layouts`
array. Each layout has a unique `name` and ordered `r1` and `r2` segment lists.
A segment is `fixed`, `capture`, or `sequence`, and every segment sets
boolean `retain`.

- **Fixed** anchors contain A/C/G/T and must match completely at their declared
  position. Each anchor tolerates one substitution by default; change the
  default with `--max-anchor-mismatches` or per anchor with `max_mismatches`.
  Anchor tolerance applies only to fixed sequences. It does not rescue or
  correct barcode values.
- **Captures** have a non-empty arbitrary `name`, a positive `length` (or
  `"rest"`), optional `normalize` (`forward`, the default, or
  `reverse_complement`), and an optional allowed `alphabet` (uppercase
  A/C/G/T/N; default ACGT).
- **Sequence** segments account for bases that are not captured; their length
  is a positive integer or `"rest"`.

A mate may have one `"rest"` segment, which accounts for the read bases not
assigned by its other segments. Retained segments must form one contiguous,
non-empty interval, and each mate must retain at least 15 bases by default
(`--min-retained-length`). Capture normalization affects metadata only: the
retained sequence and qualities stay as sequenced. Repeated captures with the
same name must agree after normalization. A pair is accepted only when exactly
one layout matches.

Example with a 6-base identity capture and a positional 7-base R1 anchor, plus
a reverse-complement-normalized R2 identity capture:

```json
{
  "schema_version": 1,
  "layouts": [{
    "name": "library_layout",
    "r1": [
      {"kind": "capture", "name": "identity_5", "length": 6, "retain": false},
      {"kind": "fixed", "sequence": "GATTACA", "retain": false},
      {"kind": "sequence", "length": "rest", "retain": true}
    ],
    "r2": [
      {"kind": "capture", "name": "identity_3", "length": 6,
       "normalize": "reverse_complement", "retain": false},
      {"kind": "sequence", "length": "rest", "retain": true}
    ]
  }]
}
```

### Barcode map and field selection

Step 2 stores all normalized named captures in a canonical `CAP1` annotation
on each mate's FASTQ name, immediately before the UMI suffix. Step 3 receives
one or more explicit `--barcode-field NAME` options. Only those fields are
interpreted as identity barcodes; other captures remain metadata. A capture
named `PID` has no built-in or automatic lookup role: any named capture
acquires identity meaning only when selected with `--barcode-field`.

The selected values are looked up exactly in the barcode map:

```text
barcode	Element
ACGCTA	Element_001
```

Every selected field must resolve to the same `Element`. Multiple barcode
values may identify one Element, but one barcode cannot identify multiple
Elements. There is no nearest-barcode rescue or error correction. Conflicting
TSV assignments, or Element IDs absent from the FASTA, fail input validation.

In the example above, the R1 capture must be `ACGCTA`; the R2 read carries its
reverse complement `TAGCGT`, which Step 2 normalizes to `ACGCTA`. Both
selected fields therefore resolve to `Element_001`, and the reference FASTA
contains an `Element_001` record whose sequence is the tested element alone.

### Element-only reference

The Step 3 FASTA contains tested-element sequences only, with unique
first-token IDs and A/C/G/T/N bases. Different barcodes may select different
Element IDs with identical sequences; identical sequences are no longer
rejected. Reference `N` is not a wildcard: any aligned N costs one edit,
including N against N.

## Coordinates and placements

Coordinates now refer to the element-only FASTA. Tracks made by earlier
releases against construct-derived references include flank and offset
coordinates, so they cannot be compared directly with new element-coordinate
tracks. Pairs that previously placed only because their reads extended into
construct flanks no longer contribute endpoints. Keep old tracks as
historical results; do not silently reinterpret them or treat regenerated
tracks as equivalent data.

Step 3 searches only the declared R1 orientation and the opposite R2
orientation; it does not search both strands and filter later. Each full
query must align with both query ends anchored to reference bases. Candidate
pairs are ranked jointly under paired geometry, so an individually non-best
mate placement can be part of the best pair. Equivalent gap paths with
identical mate spans are represented consistently; tied best distinct span
pairs are rejected as ambiguous. Pairs outside the element or without a valid
placement do not enter the main BAM.

Accepted BAM records carry the canonical capture JSON in `xc:Z` and the
resolved Element in `xe:Z`. These tags support metadata inspection; the
standard reference name and coordinate fields remain authoritative, and Step 4
does not require the tags.

Step 4 keeps paired geometry, R1-derived RNA strand, the R2 5′ cap endpoint,
the R1 5′ polymerase-position proxy, track signs, and paired UMI-tools
deduplication. Reverse-read 5′ positions use the CIGAR reference span,
including deletions; insertions do not advance reference coordinates.

## Complete command example

The example runs one plus-strand library. Run minus-strand libraries with
`--rna-strand minus` at both Steps 3 and 4.

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

Step 3 requires `samtools`; Step 4 requires `samtools`, BEDTools, and
UMI-tools. STAR and STAR indexes are no longer used or accepted. `--threads`
is a per-invocation CPU budget: Step 1 defaults to 16, Step 2 to 1, and Steps 3
and 4 to 16. Step 3 also supports `--bam-sort-memory` (default `2G`) and
`--tmp-dir` for sorting resources. These budgets bound worker activity and
batches; reference and barcode-map storage scale with those inputs, and total
process memory is not constant. See [resource guidance](resource-guidance.md).

## Outputs and diagnostics

| Step | Main outputs | Diagnostics | Summary schema |
| --- | --- | --- | --- |
| 2 | `<prefix>_R1.ident.fq.gz`, `<prefix>_R2.ident.fq.gz` | `<prefix>_step2_rejected_R1.fq.gz`, `<prefix>_step2_rejected_R2.fq.gz`, `<prefix>_step2_rejections.tsv.gz` | `2.0` in `<prefix>_step2_summary.json` |
| 3 | `<prefix>_step3_alignment.bam` and `.bai` | `<prefix>_step3_rejected_R1.fq.gz`, `<prefix>_step3_rejected_R2.fq.gz`, `<prefix>_step3_rejections.tsv.gz` | `4.0` in `<prefix>_step3_summary.json` |
| 4 | Selected `.5pl.bw`/`.3pl.bw` or `.5mn.bw`/`.3mn.bw` tracks (all four for `both`) | — | `2.0` in `<prefix>.step4_summary.json` |

Rejection tables are gzip TSVs with `read_name`, `captures`, `reason`, and
`evidence` columns. Step 2 rejected FASTQs preserve the original input pairs;
Step 3 rejected FASTQs preserve the annotated, clipped inputs. Summaries
distinguish complete diagnostics from incomplete evidence after a midstream
failure; a partially processed run must not be read as a complete rejection
audit.

Unknown barcodes, disagreeing selected identities, no in-ceiling placement,
invalid paired geometry, and tied-best placements have separate Step 3
rejection reasons. Malformed annotations, missing selected fields, or invalid
barcode-map/reference configuration fail the invocation. Zero retained Step 2
pairs or zero accepted Step 3 pairs is a failure; inspect the diagnostic files
and failed summary before changing inputs.

## Breaking-change mapping

| 0.2.0b4 input or behavior | 0.2.0b5 replacement |
| --- | --- |
| Optional `step2-clip-construct-flank` and `--clip-layout` | Mandatory `step2-identify-and-clip` with a version 1 named-capture layout via `--layout`; Step 1 FASTQs cannot bypass it |
| Construct clipping layout and fixed flank coordinates | Positional fixed anchors, arbitrary named captures, contiguous retained intervals, configurable minimum length, canonical CAP1 annotation |
| STAR reference-wide search and `--star`, `--star-index-dir`, `--max-multimaps`, `--random-seed` | Exact selected-field barcode lookup through `--barcode-map` and repeatable `--barcode-field`, then native alignment to one element-only FASTA record; removed options and command have no aliases |
| Step 3 default `--rna-strand both` | Explicit Step 3 `plus` or `minus`; give the same value to Step 4 |
| STAR edit and multimapping summaries, `effective_mapping_counts`, strand-rejected unmapped pairs | Step 3 schema 4.0 placement and rejection evidence; rejected pairs leave the main BAM; no STAR or index evidence |
| Step 4 `--max-pair-mismatches`, `mismatch_ceiling`, `mismatch_histogram`, `max_pair_mismatches` | `--max-pair-edits`, schema 2.0, `edit_ceiling`, `edit_histogram`, `max_pair_edits`, counting substituted, inserted, and deleted bases |
| Earlier Step 2/3/4 summaries and caches | Regenerate outputs in a fresh directory; do not relabel old summaries with current schema versions |
| Construct-derived coordinates and flank-supported alignments | Element-only reference coordinates; flank-only placements disappear and old/new tracks are not directly comparable |
| No Step 2/3 rejection artifacts | Paired rejected FASTQs and structured rejection TSVs with complete/incomplete diagnostic status |

Layout matching validates fixed anchors at declared positions and permits only
their configured substitutions. Identity lookup is exact: no nearest match,
barcode correction, or automatic PID lookup is performed. CAP does not infer
element boundaries from sequence or restore information removed by clipping.

## Validation and scope

Release 0.2.0b5 native CAP acceptance consists of one fresh synthetic tracked
run that executed real Steps 1–4 on the plus and minus strands at one and two
threads, with STAR absent. Each invocation reconciled 9 raw pairs to 5
accepted pairs, 4 rejected pairs, and 4 retained molecules, and independent
identity, BAM, UMI, endpoint, diagnostic, and thread-parity checks passed. No
performance threshold is asserted. This is not a real-library CAP assay PASS.
The historical four-library acceptance of release 0.2.0b3 applies only to the
earlier STAR workflow and does not certify the native workflow.

Libraries that lack a trustworthy barcode→Element map are not made compatible
by this migration; CAP does not infer barcode assignments. See [known
limitations](known-limitations.md) for the remaining scope boundaries.
