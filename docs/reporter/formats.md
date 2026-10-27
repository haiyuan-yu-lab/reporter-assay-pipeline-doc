# Reporter format contracts

These format IDs and encodings are the **0.2.0b5** public handoff contract.
Tabular
pipeline handoffs use shared **format IDs**. CLI flags that take user
paths document which format each input or output must satisfy.

Unless a format entry says otherwise:

- UTF-8 text with Unix line endings
- Tab-delimited fields
- Required header row matching the format column contract
- Optional gzip (`.tsv.gz`); readers accept compressed and uncompressed paths

Plain-text lists use one logical record per non-empty line.

## Column contract patterns

| Pattern | Meaning | Examples |
| --- | --- | --- |
| **Fixed-column** | Entire header is defined and ordered | `element-counts`, `activity-by-element` |
| **Layout-defined** | Header comes from per-sample layout schema | `delimited-records` |
| **Suffix-fixed** | Leading ID columns vary; trailing columns are fixed | `pretran-merged-counts`, `crosswalk-map` |
| **Presence-fixed** | Required column names are fixed; other columns are IDs | `orientation-resolved-pretran` |

For **suffix-fixed** formats, leading ID columns are declared via PreTran
`--id-columns` and must match the file header exactly (names and order). Do not
assume fixed names such as `EID` and `PID` in every assay configuration. The
standard dual-ID reporter-assay profile uses `EID,PID`.

## Format registry

| Format ID | Column contract | Typical producer |
| --- | --- | --- |
| `delimited-records` | Layout-defined (`column_names` from layout schema) | Step 2; optional `concat_step2_records` |
| `orientation-resolved-pretran` | `Element`, `UMI` required; ≥1 ID column | Step 3 |
| `pretran-merged-counts` | `<id-columns>…`, `Element`, `PreTranUMICount` | Step 4 |
| `crosswalk-map` | same suffix as above | Step 5 |
| `cluster-reference` | `ObservedID`, `CanonicalID`, `Element` | Step 5 |
| `posttran-matched-records` | eBC: `EID`, `UMI`; pBC: `UMI1`, `PID1`, `PID2`, `UMI2` | Step 6 |
| `posttran-quantification` | eBC: `EID`, `MoleculeCount`; pBC: `PID1`, `PID2`, `MoleculeCount` | Step 7 |
| `element-counts` | `Element`, `MoleculeCount` | Step 8 |
| `activity-by-element` | `Element`, `DNACount`, `RNACount`, `ActivityScore`, `log2FC`, `ActivityZ`, `ActivityCall`, `FittedRNADNALog2FC`, `ControlRelativeLog2FC`, `ControlRelativeSE`, `PValue`, `AdjustedPValue`, `IsNegativeControl` (**0.2.0b5**; historical **0.1.0b4** was the seven-column prefix) | Step 9 |
| `orientation-collapsed-activity` | 30 fixed columns; one row per reference pair | QC `plot_orientation_scatter` |
| `pretran-negative-control-representation` | `Element`, `Status`, `PreTranUMICount`, then `<id-columns>…` | QC `pretrans_nc_representation` |
| `negative-control-list` | One element ID per non-empty line | Reference asset |

!!! note "CLI flag naming"
    Some flags still say `--activity-output`. That path must be an
    **`activity-by-element`** table.

---

## Input formats

### `delimited-records`

Columns and order match the per-sample layout schema JSON used at Step 2.
Common PreTran layouts emit `UMI`, `EID`, `PID`, `ElementAnchorSeq`;
post-transfection layouts vary by branch. Compatible gzip-compressed tables
with identical headers may be pooled by
[`concat_step2_records`](../cli/pipe.md#concat_step2_records).

## Output and intermediate formats

### `orientation-resolved-pretran`

Must include columns named `Element` and `UMI`, plus the ID columns declared
via `--id-columns`. Dual-ID profile header order:
`EID`, `PID`, `Element`, `UMI`. EID-only: `EID`, `Element`, `UMI`.

### `pretran-merged-counts`

Suffix-fixed:

```text
<id-column-1>[, <id-column-2>, …], Element, PreTranUMICount
```

`PreTranUMICount` is a positive integer. Reporter-assay profile:
`EID`, `PID`, `Element`, `PreTranUMICount`.

### `crosswalk-map`

Same suffix-fixed contract as `pretran-merged-counts`. Typical artifact:
`pretran_step5_id_crosswalk.tsv.gz`. Leading ID columns are discovered from the
header (used by QC `--id-column`).

### `cluster-reference`

Fixed columns in order: `ObservedID`, `CanonicalID`, `Element`.

Each file is one identifier domain. Domain is conveyed by **filename**, not
column names — filenames use ExactID casing from `--id-columns` (for example
`pretran_step5_EID_cluster_reference.tsv.gz` vs
`pretran_step5_PID_cluster_reference.tsv.gz`). EID-only profiles emit only the
EID cluster file.

### `posttran-matched-records`

- eBC: `EID`, `UMI`
- pBC: `UMI1`, `PID1`, `PID2`, `UMI2`

### `posttran-quantification`

- eBC: `EID`, `MoleculeCount`
- pBC: `PID1`, `PID2`, `MoleculeCount`

`MoleculeCount` is a positive integer.

### `element-counts`

Fixed columns: `Element`, `MoleculeCount`. `Element` values are unique within a
file. Consumed by `call_activity` and `make_between_rep_activity_plot`.

### `activity-by-element`

**0.2.0b5** fixed columns in order:

`Element`, `DNACount`, `RNACount`, `ActivityScore`, `log2FC`, `ActivityZ`, `ActivityCall`, `FittedRNADNALog2FC`, `ControlRelativeLog2FC`, `ControlRelativeSE`, `PValue`, `AdjustedPValue`, `IsNegativeControl`

Final branch-specific Step 9 output (for example `EID-ActivityByElement.tsv.gz`).
The seven descriptive columns keep their original formulas as a prefix;
`ActivityCall` is `Active` / `Repressive` / `NoCall` / `Control`; control
rows carry empty `PValue` / `AdjustedPValue`; `IsNegativeControl` is lowercase
`true` / `false`. QC and export readers accept only this thirteen-column table
and reject the historical seven-column **0.1.0b4** table with a format
diagnostic. See [Step 9](../steps-9.md#released-contract-020b5) for the field
semantics.

### `orientation-collapsed-activity`

Optional QC table from `plot_orientation_scatter --table-output-path`. Exactly
`N` rows (`N` = reference record count), sorted by `PairIndex` ascending.

Columns in order:

1. `PairIndex`
2. `FwdElement`
3. `RevElement`
4. `PairCoverage`
5. `Plotted`
6. `IsNegativeControl`
7. `FwdDNACount`
8. `FwdRNACount`
9. `FwdActivityScore`
10. `FwdLog2FC`
11. `FwdActivityZ`
12. `FwdActivityCall`
13. `RevDNACount`
14. `RevRNACount`
15. `RevActivityScore`
16. `RevLog2FC`
17. `RevActivityZ`
18. `RevActivityCall`
19. `CollapsedDNACount`
20. `CollapsedRNACount`
21. `CollapsedActivityScore`
22. `CollapsedLog2FC`
23. `CollapsedActivityZ`
24. `CollapsedActivityCall`
25. `ActivityScoreDelta`
26. `ActivityZDelta`
27. `FwdControlRelativeLog2FC`
28. `RevControlRelativeLog2FC`
29. `CollapsedControlRelativeLog2FC`
30. `ControlRelativeLog2FCDelta`

Key fields:

- `PairCoverage`: `Both`, `FwdOnly`, `RevOnly`, or `Neither` (after the selected QC metric filter when `--metric ControlRelativeLog2FC`)
- `Plotted`: `true` when `PairCoverage` is `Both`; otherwise `false`
- Boolean columns use lowercase `true` / `false`
- `ActivityCall` columns use `Active` / `Repressive` / `NoCall` / `Control`
  (**0.2.0b5**). `CollapsedActivityCall` additionally uses `MixedControl`
  (control/candidate mix) or `Discordant` (opposing `Active`/`Repressive`);
  one-sided pairs retain the present call, directional calls win over
  `NoCall`, and two `NoCall` results remain `NoCall`. Historical **0.1.0b4**
  tables used `Active` or `Inactive` and are rejected by current readers.

### `pretran-negative-control-representation`

Required QC table from `pretrans_nc_representation`. Suffix-dynamic header:

```text
Element, Status, PreTranUMICount, <id-column-1>[, <id-column-2>, …]
```

Trailing ID columns reuse each input `crosswalk-map` ID-column name in input
order. **Cell values are distinct counts for that domain, not identifier
values** — do not treat this table as a second crosswalk.

One row per unique annotated negative-control `Element`, sorted lexically.
`Status` is `retained` or `missing`. Missing controls have zero
`PreTranUMICount` and zero in every dynamic ID column.

### `negative-control-list`

One element ID per non-empty line. Blank lines ignored. Required (non-empty)
for Step 9 / `call_activity` and for export `ES`. Also required for
`pretrans_nc_representation`.

---

---

### Layout schemas

This page documents the **0.2.0b5** layout-schema grammar and matching
behavior. Examples use symbolic anchors and are not executable assay inputs.

A layout schema is per-library JSON configuration consumed by Step 2. It tells
the parser how to walk R1 and R2, which variable fields to capture, which
constant anchors to verify, the output-column order, and which captured fields
to reverse-complement. The resulting header is the `column_names` list in
exactly that order.

### Grammar

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

### Matching and transformation order

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

### Canonical symbolic examples

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

### Validation rules and failure actions

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

See [Steps 1–2: prepare one library](../steps-1-2.md) for the complete individual
Step 1 → Step 2 handoff and symptom-first recovery matrix.

### Privacy boundary

Keep real construct sequences, primer/anchor strings, sample names, and
institutional paths in local files only. Public documentation examples should
use symbolic anchors and generic library prefixes such as those on this page.
