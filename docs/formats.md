# Artifact formats

These format IDs and encodings are the **0.1.0b2** public handoff contract.

Tabular pipeline handoffs use shared **format IDs**. CLI flags that take user
paths document which format each input or output must satisfy.

## Shared encoding

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
| `delimited-records` | Layout-defined (`column_names` from layout schema) | Step 2 |
| `orientation-resolved-pretran` | `Element`, `UMI` required; ≥1 ID column | Step 3 |
| `pretran-merged-counts` | `<id-columns>…`, `Element`, `PreTranUMICount` | Step 4 |
| `crosswalk-map` | same suffix as above | Step 5 |
| `cluster-reference` | `ObservedID`, `CanonicalID`, `Element` | Step 5 |
| `posttran-matched-records` | eBC: `EID`, `UMI`; pBC: `UMI1`, `PID1`, `PID2`, `UMI2` | Step 6 |
| `posttran-quantification` | eBC: `EID`, `MoleculeCount`; pBC: `PID1`, `PID2`, `MoleculeCount` | Step 7 |
| `element-counts` | `Element`, `MoleculeCount` | Step 8 |
| `activity-by-element` | `Element`, `DNACount`, `RNACount`, `ActivityScore`, `log2FC`, `ActivityZ`, `ActivityCall` | Step 9 |
| `orientation-collapsed-activity` | 26 fixed columns; one row per reference pair | QC `plot_orientation_scatter` |
| `pretran-negative-control-representation` | `Element`, `Status`, `PreTranUMICount`, then `<id-columns>…` | QC `pretrans_nc_representation` |
| `negative-control-list` | One element ID per non-empty line | Reference asset |

!!! note "CLI flag naming"
    Some flags still say `--activity-output`. That path must be an
    **`activity-by-element`** table.

---

## Format definitions

### `delimited-records`

Columns and order match the per-sample layout schema JSON used at Step 2.
Common PreTran layouts emit `UMI`, `EID`, `PID`, `ElementAnchorSeq`;
post-transfection layouts vary by branch.

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

Fixed columns in order:

`Element`, `DNACount`, `RNACount`, `ActivityScore`, `log2FC`, `ActivityZ`, `ActivityCall`

Final branch-specific Step 9 output (for example `EID-ActivityByElement.tsv.gz`).

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

Key fields:

- `PairCoverage`: `Both`, `FwdOnly`, `RevOnly`, or `Neither`
- `Plotted`: `true` when `PairCoverage` is `Both`; otherwise `false`
- Boolean columns use lowercase `true` / `false`
- `ActivityCall` columns use `Active` or `Inactive`

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
