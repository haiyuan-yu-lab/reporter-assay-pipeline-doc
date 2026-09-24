# Step 9: call activity

> **Version applicability.** The [released contract](#released-contract-010b4)
> below describes **0.1.0b4** (seven-column table, z-score calls). The
> [revised contract](#unreleased-revised-contract-control-relative-limma-voom)
> is **unreleased**: it is implemented and contract-tested but has no release
> version yet. The release map still points at 0.1.0b4 as the current release.
> Do not mix tables across contracts: new QC and export readers accept only
> the thirteen-column table and reject historical seven-column tables.

## Released contract (0.1.0b4)

Step 9 combines the element-count tables from matching PostTran DNA and RNA
replicates into one `activity-by-element` table. Run it once for each branch
that is present. A full dual-branch workflow therefore produces one eBC/EID
table and one pBC/PID table. An explicitly selected EID-only variation runs
Step 9 once and is complete only within that reduced variation; it does not
satisfy full dual-branch workflow completion. Detailed variation commands are
covered by the workflow task documentation.

The input tables must be successful Step 8 `element-counts` artifacts with the
exact header `Element\tMoleculeCount`. The negative-control annotation is a
plain-text `negative-control-list`: one non-empty `Element` ID per line, with
no header.

Each input table must also satisfy the Step 8 value contract: every `Element`
is a non-empty string, every `MoleculeCount` is a positive integer, and an
`Element` occurs at most once within that replicate. A missing or malformed
header is configuration-fatal. Individual malformed data rows may be skipped
and counted when valid rows remain, but duplicate element keys are not a valid
replicate input and must be corrected before activity calling.

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
`failure_reason`. `status` is exactly `success` or `failed`. `failure_reason`
is null on success and is required and non-null when status is `failed`.
`input_element_count_min` is the smallest
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
not make a failed summary complete. For the full dual-branch workflow, if one
branch fails, do not treat the other branch's successful output as evidence
that the failed branch is biologically inactive: both branch invocations must
report success. Downstream QC and export should consume only a successful,
contract-conforming `activity-by-element` table.

## Unreleased revised contract (control-relative limma–voom)

The revised contract keeps the same branch layout — run once per branch, one
primary table plus one JSON summary per branch — but replaces the z-score call
with a control-relative limma–voom fit. It has no release version yet.

### Legacy descriptive versus fitted fields

The thirteen-column table keeps the seven legacy descriptive columns with
their original formulas, then appends six explicitly named model fields. The
two groups live on different reference scales and are not interchangeable:

| Column | Group | Meaning |
| --- | --- | --- |
| `Element` | — | Retained element identifier |
| `DNACount` | legacy | Mean DNA count across DNA libraries (imputed zeros included) |
| `RNACount` | legacy | Mean RNA count across RNA libraries (imputed zeros included) |
| `ActivityScore` | legacy | Mean replicate `log2((RNA + p) / (DNA + p))` with `--pseudocount` |
| `log2FC` | legacy | `ActivityScore` minus the median control `ActivityScore` |
| `ActivityZ` | legacy | Control-mean/SD z-score of `ActivityScore`; empty with a warning when the control SD is zero |
| `ActivityCall` | fitted | `Active`, `Repressive`, `NoCall`, or `Control` (model rules below) |
| `FittedRNADNALog2FC` | fitted | Fitted RNA-versus-DNA log2 coefficient (normalized reporter expression) |
| `ControlRelativeLog2FC` | fitted | `FittedRNADNALog2FC` minus the fitted control median |
| `ControlRelativeSE` | fitted | Moderated standard error of the fitted coefficient |
| `PValue` | fitted | Two-sided p-value for equality with the control baseline (candidates only) |
| `AdjustedPValue` | fitted | Benjamini–Hochberg adjusted p-value within the invocation (candidates only) |
| `IsNegativeControl` | fitted | Lowercase `true` / `false`; `true` exactly for `Control` rows |

Control rows show fitted effects for inspection but carry empty `PValue` and
`AdjustedPValue`. `ActivityCall` no longer uses `Active` / `Inactive`, and the
`--activity-threshold-z` flag is retired.

### Null hypothesis and conditional inference

The null for each candidate is **equality with the fitted negative-control
baseline** (the median fitted control coefficient), not a zero RNA/DNA
coefficient. This answers whether the element differs from observed intrinsic
reporter activity, which need not be zero. The p-value is computed for that
shifted null; it is never copied from a zero-coefficient test.

Inference is **conditional**: the TMM normalization factors, the control
median baseline, and (at three or more pairs) the consensus correlation and
library quality weights are treated as fixed estimated inputs. Their
uncertainty is not propagated into the p-value.

### Pairing, filters, and weighting modes

- DNA/RNA lists must have equal length with at least two pairs; position `i`
  of each list is biological replicate pair `i`. One-pair runs and unequal
  lengths fail.
- The element universe is the union of IDs observed in any valid input; an
  absent row for an otherwise observed element counts as zero molecules.
  Malformed, duplicate, nonpositive, or unreadable rows fail instead of
  becoming zeros.
- Candidates and controls share the DNA representation rule: total raw DNA
  count at least `--min-total-dna-count` (default `50`) and detection in at
  least `--min-dna-replicates` DNA libraries (default `2`). Eligible RNA zeros
  are kept. A controls-only retained set fails.
- TMM factors are estimated across all DNA and RNA libraries with
  control-guided trimming; each library-to-reference comparison needs at least
  `--min-usable-controls` usable controls (default `20`). Unsupported
  comparisons fail rather than falling back to unity factors.
- Exactly two pairs fit with ordinary voom and fixed replicate blocks (no
  `duplicateCorrelation`, which is inestimable with two blocks). Three or more
  pairs fit with `voomWithQualityWeights` plus `duplicateCorrelation`
  replicate blocking, and the summary records the consensus correlation and
  per-library quality weights.
- Candidate p-values get one Benjamini–Hochberg correction per invocation.
  eBC and pBC run separately with no joint correction.
- Calls: `Control` for eligible controls; `Active` when the control-relative
  effect is strictly above `--min-absolute-log2-effect` (default `1.0`) with
  `AdjustedPValue <= --max-adjusted-p` (default `0.05`); `Repressive` when
  strictly below the negative threshold with the same p condition; otherwise
  `NoCall`, including effects exactly at either threshold.

### R dependencies

Step 9 shells out to `Rscript` — no Python approximation is substituted.
`edgeR` and `limma` are always required; `statmod` is additionally required
for three-or-more-pair fits (it provides `duplicateCorrelation`). Missing
dependencies fail before fitting with an actionable message. Installed R and
package versions are recorded in the JSON summary.

### Defaults, warnings, and artifacts

| Flag | Default | Meaning |
| --- | --- | --- |
| `--pseudocount` | `1.0` | Pseudocount for legacy log ratios only |
| `--min-absolute-log2-effect` | `1.0` | Strict magnitude boundary for calls |
| `--max-adjusted-p` | `0.05` | Adjusted-p ceiling for calls |
| `--min-total-dna-count` | `50` | Minimum summed raw DNA count |
| `--min-dna-replicates` | `2` | Minimum detecting DNA libraries |
| `--min-usable-controls` | `20` | Minimum usable controls per TMM comparison |
| `--filtered-elements-output-path` | none | Optional `.tsv` / `.tsv.gz` audit sidecar |

When the legacy control `ActivityScore` standard deviation is zero, the fitted
model still runs: `ActivityZ` is left empty and the summary carries a warning
naming `ActivityZ`. Requesting that missing metric downstream
(`plot_orientation_scatter --metric activityZ`, or an `ActivityZ`
`--anno-track` in export) fails with a diagnostic pointing at usable
alternatives.

Default artifacts per branch are exactly one activity table plus one JSON
summary (which records counts, exclusions by reason, thresholds, control
median, TMM reference/factors/support, model mode, testing family, R/package
versions, warnings, and paths). The filtered-elements sidecar — one row per
excluded element with DNA total, detection count, control status, and all
exclusion reasons — is written only when `--filtered-elements-output-path`
is supplied. Orientation QC (`plot_orientation_scatter`) remains a separate
command and is never emitted automatically by Step 9.

### Failed-run recovery (revised contract)

| Symptom | Next valid action |
| --- | --- |
| Unequal DNA/RNA list lengths, fewer than two pairs, bad thresholds, missing `Rscript`/edgeR/limma (or statmod at 3+ pairs) | Correct the command or environment, then rerun. The failed summary names the cause. |
| Malformed rows, duplicate IDs, nonpositive counts | Fix the damaged Step 8 table; corruption is never treated as zero. |
| Too few usable controls for a TMM comparison, or a non-finite factor | Supply more eligible controls or lower `--min-usable-controls`; rerun. |
| No eligible candidate, or controls-only retained set | Repair upstream retention or the control list; rerun. |
| `ActivityZ` empty with a summary warning | Inference still succeeded; use `activity_score` or fitted columns downstream. |
| Summary says `failed` | Read `failure_reason` first, fix that condition, and rerun before QC/export. |
