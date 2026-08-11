# Layout-schema reference

A layout schema is per-library JSON configuration consumed by Step 2. It tells
the parser how to walk R1 and R2, which variable fields to capture, which
constant anchors to verify, the output-column order, and which captured fields
to reverse-complement. The resulting header is the `column_names` list in
exactly that order.

## Grammar

Each of `layout1` and `layout2` is an ordered list of tokens:

| Token | Meaning | Output |
| --- | --- | --- |
| Positive integer `L` | Capture the next `L` bases from this read | One value, in the next `column_names` slot |
| String `A` | Match constant anchor `A` at the current cursor | No value |
| `-1` | Capture the remainder of the read | One value, in the next `column_names` slot |

Capture tokens across `layout1`, then `layout2`, are assigned to
`column_names` in encounter order. The number of capture tokens must therefore
equal the number of output columns. Constant anchors are not output columns.
Use JSON numbers for lengths and JSON strings for anchors and field names.
`column_names` and `reverse_complements` are ordered JSON string arrays (the
released parser also accepts the documented legacy space-delimited form).

Required top-level keys are:

```json
{
  "layout1": [],
  "layout2": [],
  "column_names": []
}
```

`reverse_complements` is optional and defaults to an empty list. Every name in
it must occur in `column_names`; otherwise configuration validation fails.

## Matching and transformation order

For each synchronized R1/R2 pair, Step 2:

1. Walks `layout1` on R1 and `layout2` on R2 from left to right.
2. Captures each integer or remainder token and checks each constant anchor.
3. Applies `max_edit_distance` to anchor matching (default `1`). Non-final
   anchors must match their full span within that tolerance.
4. Allows a final anchor to end beyond a right-trimmed read when the observed
   overlap is at least `min_last_anchor_match` (default `10`) and its mismatch
   count is within the tolerance. This partial-match rule applies only to the
   terminal anchor.
5. Assigns captured values to `column_names` in encounter order.
6. Reverse-complements only the named captured fields, after extraction. The
   source read is not reverse-complemented before cursor traversal, and
   constant anchors are not output fields.

An extraction mismatch skips that pair and increments the mismatch summary;
it does not by itself make the invocation fail. A malformed schema, corrupt
FASTQ, pair desynchronization, or zero retained records is fatal.

## Canonical symbolic examples

The following examples use invented symbolic anchors (`ANCHOR_*`) and capture
lengths. They show grammar and field relationships only; they are not assay
constructs or executable input files.

### PreTran dual-ID schema

This schema emits `UMI`, `EID`, `PID`, and `ElementAnchorSeq` in that order.

```json
{
  "layout1": [12, "ANCHOR_PRE_A", 20, "ANCHOR_PRE_B"],
  "layout2": ["ANCHOR_PRE_C", 20, "ANCHOR_PRE_D", -1],
  "column_names": ["UMI", "EID", "PID", "ElementAnchorSeq"],
  "reverse_complements": ["PID", "ElementAnchorSeq"]
}
```

`layout1` contributes `UMI` then `EID`; `layout2` contributes `PID` then
`ElementAnchorSeq`. After extraction, only `PID` and `ElementAnchorSeq` are
reverse-complemented. The resulting Step 2 file is the `delimited-records`
input expected by Step 3. The dual-ID PreTran steps must consistently declare
`--id-columns EID,PID`.

### eBC schema

The eBC branch uses the EID domain and emits two captures:

```json
{
  "layout1": [12, "ANCHOR_EBC_A", 20, "ANCHOR_EBC_B"],
  "layout2": ["ANCHOR_EBC_C", -1],
  "column_names": ["UMI", "EID"],
  "reverse_complements": ["UMI", "EID"]
}
```

The next command is the eBC `process_posttrans` path after Step 1 and Step 2
have succeeded. Use the same schema shape for each eBC DNA/RNA replicate only
when the libraries truly share this read layout.

### pBC schema

The pBC branch uses the PID domain and emits paired PID/UMI fields:

```json
{
  "layout1": [12, "ANCHOR_PBC_A", 20, "ANCHOR_PBC_B"],
  "layout2": ["ANCHOR_PBC_C", 20, "ANCHOR_PBC_D", 12],
  "column_names": ["UMI1", "PID1", "PID2", "UMI2"],
  "reverse_complements": ["PID1", "UMI1"]
}
```

The encounter order is `UMI1`, `PID1` from R1 followed by `PID2`, `UMI2`
from R2. Reverse-complementing is applied only to `PID1` and `UMI1` after all
four values are captured. The next command is the pBC PostTran path; a pBC
schema does not turn the library into an eBC input.

## Validation rules and failure actions

| Check | Valid condition | If it fails |
| --- | --- | --- |
| Required keys | `layout1`, `layout2`, `column_names` exist and are lists | Stop before Step 2; repair JSON |
| Capture count | Capture tokens equal `column_names` length | Stop; output header cannot be formed |
| Reverse-complement names | Every name is an output column | Stop; remove or correct the unknown name |
| Anchor tolerance | `max_edit_distance` is non-negative; terminal overlap meets `min_last_anchor_match` | Stop or adjust the invocation deliberately |
| Input schema match | FASTQ pair and library type match the schema | Stop; do not reinterpret reads with another schema |
| Extraction result | At least one record is retained | Step 2 fails; inspect anchors, read direction, and trimming |

The valid next command after schema validation is Step 2 or its grouped
wrapper, for example `prep_lib` with `--layout-schema`. After it succeeds,
verify `*_step2_records.tsv.gz`, its header, and `*_step2_summary.json` before
using the records in Step 3 or Step 6.

## Privacy boundary

Keep real construct sequences, primer/anchor strings, sample names, and
institutional paths in local files only. Public documentation examples should
use symbolic anchors and generic library prefixes such as those on this page.
