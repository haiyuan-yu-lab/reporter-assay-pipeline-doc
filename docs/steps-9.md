# Step 9: call activity

> **Version applicability.** This page documents **0.2.0b1**. The
> [released contract](#released-contract-020b1) is the control-relative
> limma–voom table (thirteen columns). Historical
> [0.1.0b4](#historical-contract-010b4) used a seven-column z-score table.
> Do not mix tables across contracts: QC and export readers accept only
> the thirteen-column table and reject historical seven-column tables.

## Released contract (0.2.0b1)

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
header is configuration-fatal. Malformed, duplicate, nonpositive, or
unreadable data rows fail the invocation; they are never treated as zero
counts.

This release keeps the same branch layout — one primary table plus one JSON
summary per branch — and assigns `ActivityCall` from a control-relative
limma–voom fit.

## Run one branch

DNA and RNA paths are positional biological replicate pairs. Supply the same
number of paths in the same replicate order. At least two pairs are required.
The following commands use three replicates; repeat the pattern for the
number of pairs actually present.

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
`--pseudocount` (default `1.0`) applies only to the legacy descriptive log
ratios. Fitted-call flags default to `--min-absolute-log2-effect 1.0`,
`--max-adjusted-p 0.05`, `--min-total-dna-count 50`, `--min-dna-replicates 2`,
and `--min-usable-controls 20`. The summary path defaults to
`<output directory>/<output stem>_step9_summary.json`, or can be set with
`--summary-path`.

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

Do not infer completion from a file existing. One branch is complete only when
its table is non-empty, has the exact thirteen-column header above, and its
summary reports `status=success`. Workflow completion requires all present
branches to succeed.

### Failures and recovery

| Symptom | Next valid action |
| --- | --- |
| Unequal DNA/RNA list lengths, fewer than two pairs, bad thresholds, missing `Rscript`/edgeR/limma (or statmod at 3+ pairs) | Correct the command or environment, then rerun. The failed summary names the cause. |
| Malformed rows, duplicate IDs, nonpositive counts | Fix the damaged Step 8 table; corruption is never treated as zero. |
| Too few usable controls for a TMM comparison, or a non-finite factor | Supply more eligible controls or lower `--min-usable-controls`; rerun. |
| No eligible candidate, or controls-only retained set | Repair upstream retention or the control list; rerun. |
| `ActivityZ` empty with a summary warning | Inference still succeeded; use `activity_score` or fitted columns downstream. |
| Summary says `failed` | Read `failure_reason` first, fix that condition, and rerun before QC/export. |

For the full dual-branch workflow, if one branch fails, do not treat the other
branch's successful output as evidence that the failed branch is biologically
inactive: both branch invocations must report success. Downstream QC and
export should consume only a successful, contract-conforming
`activity-by-element` table.

## Historical contract (0.1.0b4)

The 0.1.0b4 z-score contract is historical. New QC and export readers reject
its seven-column table. The text below is retained so 0.1.0b4 artifacts can
still be interpreted.

DNA and RNA paths were positional replicates with equal, non-zero length. The
retained element set was the deterministic intersection of `Element` values in
**every** DNA and RNA input table. Elements absent from any replicate were not
scored or emitted. Individual malformed data rows could be skipped and counted
when valid rows remained.

For each retained element `e` and pair `i`, with pseudocount `p`:

```text
ratio_i(e)     = (RNA_i(e) + p) / (DNA_i(e) + p)
log2_ratio_i(e) = log2(ratio_i(e))
DNACount(e)    = mean(DNA_1(e), ..., DNA_R(e))
RNACount(e)    = mean(RNA_1(e), ..., RNA_R(e))
ActivityScore(e) = mean(log2_ratio_1(e), ..., log2_ratio_R(e))
```

Only retained controls could establish the baseline. If `C` is the set of
annotated negative-control elements in the retained space, Step 9 computed:

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

When `NC_Std == 0`, `ActivityZ` was `0.0` for every element only if all
retained activity scores equaled `NC_Mean`. If scores were not constant,
normalization was undefined and the invocation failed. Finally,
`ActivityCall` was `Active` when `ActivityZ >= --activity-threshold-z`, and
`Inactive` otherwise.

The emitted rows contained exactly:

| Column | Meaning | Allowed values |
| --- | --- | --- |
| `Element` | Element in the shared intersection | non-empty identifier |
| `DNACount` | Mean DNA molecule count | non-negative numeric |
| `RNACount` | Mean RNA molecule count | non-negative numeric |
| `ActivityScore` | Mean replicate log2 ratio | finite numeric |
| `log2FC` | ActivityScore minus control median | finite numeric |
| `ActivityZ` | Control-normalized z-score | finite numeric |
| `ActivityCall` | Thresholded ActivityZ | `Active` or `Inactive` |

Optional `--pseudocount` and `--activity-threshold-z` defaulted to `1.0` and
`2.0`. Completion required a non-empty seven-column table and a successful
summary.
