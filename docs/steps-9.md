# Step 9: call activity

Step 9 combines the element-count tables from matching PostTran DNA and RNA
replicates into one `activity-by-element` table. Run it once for each branch
that is present. A full dual-branch assay therefore produces one eBC/EID table
and one pBC/PID table; an EID-only assay produces only the eBC table.

The input tables must be successful Step 8 `element-counts` artifacts with the
exact header `Element\tMoleculeCount`. The negative-control annotation is a
plain-text `negative-control-list`: one non-empty `Element` ID per line, with
no header.

## Run one branch

DNA and RNA paths are positional replicates. Supply the same number of paths
in the same replicate order. The following commands use three replicates;
repeat the pattern for the number of replicates actually present.

```bash
yulab_reporter_pipe call_activity \
  --dna-records \
    work/posttran_element_mapping/eBC_DNA_rep1_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/eBC_DNA_rep2_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/eBC_DNA_rep3_step8_element_counts.tsv.gz \
  --rna-records \
    work/posttran_element_mapping/eBC_RNA_rep1_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/eBC_RNA_rep2_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/eBC_RNA_rep3_step8_element_counts.tsv.gz \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --output-path "<out_dir>/EID-ActivityByElement.tsv.gz"
```

For pBC, use the pBC Step 8 tables and name the output
`PID-ActivityByElement.tsv.gz`:

```bash
yulab_reporter_pipe call_activity \
  --dna-records \
    work/posttran_element_mapping/pBC_DNA_rep1_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/pBC_DNA_rep2_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/pBC_DNA_rep3_step8_element_counts.tsv.gz \
  --rna-records \
    work/posttran_element_mapping/pBC_RNA_rep1_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/pBC_RNA_rep2_step8_element_counts.tsv.gz \
    work/posttran_element_mapping/pBC_RNA_rep3_step8_element_counts.tsv.gz \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --output-path "<out_dir>/PID-ActivityByElement.tsv.gz"
```

The complete CLI is documented in the [Pipeline CLI reference](cli/pipe.md).
Optional `--pseudocount` and `--activity-threshold-z` values default to `1.0`
and `2.0`; both accept values greater than or equal to zero. The summary path
defaults to `<output directory>/<output stem>_step9_summary.json`, or can be
set with `--summary-path`.

## Retained analysis space and calculation

Let `R` be the number of DNA/RNA replicate pairs. The DNA and RNA lists must
have equal, non-zero length and are paired by index. The retained element set
is the deterministic intersection of `Element` values in **every** DNA and
RNA input table. Elements absent from any replicate are not scored or emitted.

For each retained element `e` and pair `i`, with pseudocount `p`:

```text
ratio_i(e)     = (RNA_i(e) + p) / (DNA_i(e) + p)
log2_ratio_i(e) = log2(ratio_i(e))
DNACount(e)    = mean(DNA_1(e), ..., DNA_R(e))
RNACount(e)    = mean(RNA_1(e), ..., RNA_R(e))
ActivityScore(e) = mean(log2_ratio_1(e), ..., log2_ratio_R(e))
```

Only retained controls can establish the baseline. If `C` is the set of
annotated negative-control elements in the retained space, Step 9 computes:

```text
NC_Mean   = mean(ActivityScore(c) for c in C)
NC_Median = median(ActivityScore(c) for c in C)
NC_Std    = population standard deviation(ActivityScore(c) for c in C)
log2FC(e) = ActivityScore(e) - NC_Median
```

When `NC_Std > 0`:

```text
ActivityZ(e) = (ActivityScore(e) - NC_Mean) / NC_Std
```

When `NC_Std == 0`, `ActivityZ` is `0.0` for every element only if all
retained activity scores equal `NC_Mean`. If scores are not constant,
normalization is undefined and the invocation fails. Finally,
`ActivityCall` is `Active` when `ActivityZ >= --activity-threshold-z`, and
`Inactive` otherwise. The comparison is inclusive and deterministic; it is a
calculation label, not a biological claim.

The emitted `activity-by-element` rows are deterministic and contain exactly:

| Column | Meaning | Allowed values |
| --- | --- | --- |
| `Element` | Element in the shared intersection | non-empty identifier |
| `DNACount` | Mean DNA molecule count | non-negative numeric |
| `RNACount` | Mean RNA molecule count | non-negative numeric |
| `ActivityScore` | Mean replicate log2 ratio | finite numeric |
| `log2FC` | ActivityScore minus control median | finite numeric |
| `ActivityZ` | Control-normalized z-score | finite numeric |
| `ActivityCall` | Thresholded ActivityZ | `Active` or `Inactive` |

## Summary and completion

Step 9 writes one primary table and one JSON summary. A successful summary has
`status: "success"` and includes these fields:

`dna_records_paths`, `rna_records_paths`,
`negative_control_annotation_path`, `output_records_path`, `replicate_count`,
`pseudocount`, `activity_threshold_z`, `input_element_count_min`,
`retained_element_count`, `negative_control_count`,
`negative_control_retained_count`, `nc_mean`, `nc_median`, `nc_std`,
`skipped_missing_field_count`, `skipped_invalid_row_count`, `status`, and
`failure_reason` (null on success). `input_element_count_min` is the smallest
input table element count; `retained_element_count` is the size of the shared
intersection.

Do not infer completion from a file existing. One branch is complete only when
its table is non-empty, has the exact seven-column header above, and its
summary reports `status=success`. Workflow completion requires all present
branches to succeed.

## Failures and recovery

| Symptom | Class | Next valid action |
| --- | --- | --- |
| Missing required flag, unequal DNA/RNA list lengths, missing path, invalid negative value, or missing required input columns | Configuration-fatal | Correct the command or input selection, then rerun Step 9. |
| A row has missing fields, malformed values, or a non-positive count, while valid rows remain | Row-tolerated | Inspect `skipped_*` summary counts; continue only if the invocation succeeds and controls remain. |
| Input is unreadable/corrupt, or output cannot be written | Fatal I/O/parse | Fix permissions, paths, or the damaged table; rerun the failed invocation. |
| No elements remain after the all-replicate intersection | Empty-intersection failure | Compare Step 8 headers/element IDs across replicates, repair the upstream replicate(s), and rerun. |
| No annotated controls remain in the intersection | Missing-control failure | Use the correct branch-matched control list or repair upstream retention; rerun. |
| `NC_Std == 0` but retained ActivityScore values differ | Undefined-normalization failure | Inspect counts and controls; correct the inputs or choose a valid control set, then rerun. |
| Summary says `failed` or the output is empty/schema-invalid | Completion failure | Read `failure_reason` first, fix that reported condition, and rerun Step 9 before downstream QC/export. |

Some malformed rows are intentionally skipped and counted; that tolerance does
not make a failed summary complete. If one branch fails, do not treat the other
branch's successful output as evidence that the failed branch is biologically
inactive. Downstream QC and export should consume only a successful,
contract-conforming `activity-by-element` table.
