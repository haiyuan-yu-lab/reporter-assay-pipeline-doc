# Artifact formats

These format IDs and encodings are the **0.1.0b4** public handoff contract,
except for the explicitly marked **unreleased** Step 9 revision below. Tabular
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
| `activity-by-element` | `Element`, `DNACount`, `RNACount`, `ActivityScore`, `log2FC`, `ActivityZ`, `ActivityCall` (**0.1.0b4**; unreleased revision appends six fitted columns — see definition) | Step 9 |
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
post-transfection layouts vary by branch. Compatible gzip-compressed tables
with identical headers may be pooled by
[`concat_step2_records`](cli/pipe.md#concat_step2_records).

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

**0.1.0b4** fixed columns in order:

`Element`, `DNACount`, `RNACount`, `ActivityScore`, `log2FC`, `ActivityZ`, `ActivityCall`

Final branch-specific Step 9 output (for example `EID-ActivityByElement.tsv.gz`).

**Unreleased revision** (no release version yet): the seven columns above are
retained as the prefix with their original formulas, followed by
`FittedRNADNALog2FC`, `ControlRelativeLog2FC`, `ControlRelativeSE`, `PValue`,
`AdjustedPValue`, `IsNegativeControl` in that order. `ActivityCall` becomes
`Active` / `Repressive` / `NoCall` / `Control`; control rows carry empty
`PValue` / `AdjustedPValue`; `IsNegativeControl` is lowercase `true` /
`false`. New QC and export readers accept only this thirteen-column table and
reject the seven-column table with a format diagnostic. See
[Step 9](steps-9.md#unreleased-revised-contract-control-relative-limma-voom)
for the field semantics.

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
- `ActivityCall` columns use `Active` or `Inactive` (**0.1.0b4**). Under the
  unreleased Step 9 revision they use `Active` / `Repressive` / `NoCall` /
  `Control`, and `CollapsedActivityCall` additionally uses `MixedControl`
  (control/candidate mix) or `Discordant` (opposing `Active`/`Repressive`);
  one-sided pairs retain the present call, directional calls win over
  `NoCall`, and two `NoCall` results remain `NoCall`.

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

## Cap-selection Step 4 outputs

These encodings apply to `cap-assay-pipeline step4-post-alignment-processing`
only. They are not reporter-assay Step 4 tables.

### Cap-selection Step 4 bigWig tracks

Strand-selected bigWig files per successful library, where `S` is `--library-prefix`:

| Filename | Track key | Endpoint | Biological RNA strand | Published when |
| --- | --- | --- | --- | --- |
| `S.5pl.bw` | `cap_plus` | R2 sequenced 5′ (cap signal) | Plus | `both`, `plus` |
| `S.5mn.bw` | `cap_minus` | R2 sequenced 5′ (cap signal) | Minus | `both`, `minus` |
| `S.3pl.bw` | `proxy_plus` | R1 sequenced 5′ → RNA 3′ proxy | Plus | `both`, `plus` |
| `S.3mn.bw` | `proxy_minus` | R1 sequenced 5′ → RNA 3′ proxy | Minus | `both`, `minus` |

**Coordinate system:** Sequence names and lengths match the admitted BAM `@SQ`
dictionary exactly (same order as the BAM header). Intervals are **one-base**
`[start, end)` blocks on those sequences.

**Values:** Raw observation counts at each occupied position. Plus-strand
tracks (`*.5pl.bw`, `*.3pl.bw`) store **positive** integers. Minus-strand
tracks (`*.5mn.bw`, `*.3mn.bw`) store **negative** integers whose absolute
values are observation counts. **Zero-valued intervals are omitted** from the
files; absence of an interval means zero observations at that position.

Strand tracks selected by `both` with no observations still publish a valid
bigWig containing the full BAM sequence dictionary when at least one pair
is eligible. Tracks omitted by a `plus`/`minus` policy are absent from the
output directory rather than header-only.

### Cap-selection Step 4 summary JSON

File: `S.step4_summary.json` (`schema_version` `1.0`, `step`:
`step4-post-alignment-processing`).

Stable fields on success (native JSON types; unavailable values at failure time
are `null`, not fabricated zeroes):

| Field | Meaning |
| --- | --- |
| `library_prefix` | Same as CLI |
| `package_version` | Installed distribution version |
| `status` | `success` or `failed` |
| `warnings` | Array (may be empty) |
| `failure_reason` | `null` on success; concise message on failure |
| `rna_strand` | Selected policy: `both`, `plus`, or `minus` |
| `contradictory_pairs` | Otherwise eligible opposite-strand pair count when pair auditing completed, else `null` |
| `input_bam`, `output_dir` | Resolved paths |
| `tracks` | Object with all four keys (`cap_plus`, `cap_minus`, `proxy_plus`, `proxy_minus`); policy-omitted tracks are `null` |
| `summary` | Path to this JSON file |
| `samtools`, `samtools_version` | Resolved executable and probed version |
| `bedtools`, `bedtools_version` | Resolved executable and probed version |
| `pybigwig_version` | pyBigWig version when known |
| `effective_arguments` | `threads`, `max_pair_mismatches`, `rna_strand` |
| `bam_sequences` | `{name, length}` list from BAM `@SQ` |
| `read_group_id` | Read group ID (equals library prefix when admitted) |
| `pair_total_groups` | Distinct query names collated |
| `eligible_pairs` | Pairs passing all filters |
| `rejected_pairs` | Count of rejected pairs |
| `rejection_counts` | Map with keys `excluded_flags`, `mapping_completeness`, `uniqueness`, `cigar`, `mismatch_ceiling`, `geometry` |
| `mismatch_histogram` | String keys of combined `NM(R1)+NM(R2)` → pair count |
| `track_observations` | Per-track observation totals (`cap_plus`, `cap_minus`, `proxy_plus`, `proxy_minus`); selected cap and proxy groups each equal `eligible_pairs`; omitted tracks are `0` |
| `track_occupied_positions` | Distinct genomic positions with signal per track (`0` for omitted tracks) |
| `maximum_absolute_pileup` | Max pileup magnitude per track (`0` for omitted tracks) |
| `artifact_hashes` | SHA-256 per published bigWig track key (`null` for omitted tracks) |

Pure usage errors do not create a summary. An existing summary file is never
overwritten.
