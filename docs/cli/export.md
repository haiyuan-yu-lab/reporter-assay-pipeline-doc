# `yulab_reporter_export`

This page documents the `0.1.0b3` ExogeneousSequences export contract. Run the
export after a successful Step 9 `call_activity` invocation. It creates one
reference-ordered FASTA and one ExogeneousSequences **stat** annotation array
for each requested activity column.

```bash
yulab_reporter_export --help
yulab_reporter_export ES --help
```

## Inputs

`ES` requires all of the following arguments:

| Flag | Contract |
| --- | --- |
| `--activity-output PATH` | A Step 9 `activity-by-element` table. |
| `--reference PATH` | A tested-library FASTA; repeat at least once. Occurrences are ordered by their CLI order. |
| `--negative-control-annotation PATH` | A readable text file with at least one negative-control `Element` ID on each non-empty line. |
| `--output-fasta PATH` | Destination FASTA path. Its parent directory may be created. |
| `--anno-track COLUMN OUTPUT_NPY_PATH` | A requested numeric activity column and its `.npy` destination; repeat at least once. |

The `activity-by-element` input has the Step 9 columns `Element`, `DNACount`,
`RNACount`, `ActivityScore`, `log2FC`, `ActivityZ`, and `ActivityCall`. The
supported annotation columns are the exact, case-sensitive names
`ActivityScore`, `log2FC`, `ActivityZ`, `DNACount`, and `RNACount`. Each column
may be requested only once; at least one must be requested.

The negative-control list uses the same `Element` identifier namespace as the
activity table. Blank lines are ignored. A file with no usable IDs is invalid.

## Reference selection, validation, and ordering

Each FASTA header is treated as an `Element` identifier. Headers must be unique
within a FASTA, and header sets from different `--reference` files must be
pairwise disjoint. Every `Element` in the activity table must occur in exactly
one supplied reference set; an activity element absent from all references is a
validation failure. ES export does not use the forward/reverse positional-pair
contract from `SPEC-001` and does not require equal record counts.

The output FASTA is scanned deterministically in this order:

1. each `--reference` in the order it appears on the command line; then
2. each record within that FASTA in its original order.

A reference record is exported only if it has a matching activity row, is not
listed as a negative control, and has a finite numeric value in **every**
requested `--anno-track` column. Records without activity rows, negative
controls, and records failing finite-value filtering are skipped. Missing
activity records are skipped silently. A zero-record result is an invocation
failure.

## Outputs and alignment

The output FASTA retains each source header and sequence, with one record per
exported element. If `M` records are exported, every annotation file is a
NumPy `float64` array with shape `(M, 1)`. Row `j` of every array corresponds
to FASTA record `j` in the ordering above. These are scalar **stat**
annotations, not per-position tracks, and can be loaded with
`ExogeneousSequences.load_region_anno_from_npy(name, path, anno_type="stat")`.

Successful output writes are atomic. Treat the command as complete only when it
returns exit code 0 and the FASTA plus every requested `.npy` file exists and
has the expected row count and shape.

## Export once per present assay branch

Run ES independently for every branch whose Step 9 activity table was produced.
Use the matching table and branch-specific output names; do not combine eBC and
pBC rows into one invocation.

| Assay branch | Matching activity-by-element table | Identifier domain |
| --- | --- | --- |
| eBC | `EID-ActivityByElement` | EID |
| pBC | `PID-ActivityByElement` | PID |

The following dual-reference command is a complete generic template. Replace
`<activity_table>` and `<export_prefix>` with the matching branch values from
the table above. It uses generic activity, reference, control, FASTA, and
annotation-array names.

```bash
yulab_reporter_export ES \
  --activity-output "<activity_dir>/<activity_table>.tsv.gz" \
  --reference "<reference_dir>/reference-cw.fa" \
  --reference "<reference_dir>/reference-ccw.fa" \
  --negative-control-annotation "<control_dir>/negative-control-elements.txt" \
  --output-fasta "<export_dir>/<export_prefix>-reference.fa" \
  --anno-track ActivityScore "<export_dir>/<export_prefix>-activity-score.npy" \
  --anno-track log2FC "<export_dir>/<export_prefix>-log2fc.npy" \
  --anno-track ActivityZ "<export_dir>/<export_prefix>-activity-z.npy" \
  --anno-track DNACount "<export_dir>/<export_prefix>-dna-count.npy" \
  --anno-track RNACount "<export_dir>/<export_prefix>-rna-count.npy"
```

For a single-orientation/CW-only branch, omit the second reference. The
remaining ordering, validation, filtering, and array alignment rules are
unchanged:

```bash
yulab_reporter_export ES \
  --activity-output "<activity_dir>/<activity_table>.tsv.gz" \
  --reference "<reference_dir>/reference-cw.fa" \
  --negative-control-annotation "<control_dir>/negative-control-elements.txt" \
  --output-fasta "<export_dir>/<export_prefix>-reference.fa" \
  --anno-track ActivityScore "<export_dir>/<export_prefix>-activity-score.npy" \
  --anno-track log2FC "<export_dir>/<export_prefix>-log2fc.npy" \
  --anno-track ActivityZ "<export_dir>/<export_prefix>-activity-z.npy"
```

For a dual eBC and pBC assay, run the dual-reference command twice: once with
`EID-ActivityByElement` / an eBC prefix and once with
`PID-ActivityByElement` / a pBC prefix. For an EID-only assay, run only the eBC
invocation and omit the pBC invocation.

## Validation failures and recovery

The command returns non-zero for missing required arguments, unreadable or
malformed inputs, duplicate FASTA headers, overlapping headers between
references, activity elements absent from the reference union, an empty
negative-control list, unsupported or duplicate annotation columns, no
annotation tracks, zero exportable records, or output-write failures. Error
messages identify the relevant path, element, or column where available.

When it fails, preserve the inputs and read the reported constraint. Confirm
that the activity table is the successful Step 9 output for the same branch,
that every activity element is represented in one reference, that reference
headers are unique/disjoint, and that the control list is non-empty. Then rerun
with corrected inputs and fresh output paths. A non-zero exit is not a
completed export; downstream consumers must not use partial output files.

## Unsupported legacy reference options

In `0.1.0b3`, `--forward-reference` and `--reverse-reference` are unsupported
and are rejected; they are not aliases or available alternatives. Use one or
more repeatable `--reference` arguments in the desired export order. The
forward/reverse positional pairing rule remains relevant to dual-orientation
QC, but not to ES export.
