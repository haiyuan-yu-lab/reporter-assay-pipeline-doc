# `yulab_reporter_qc`

Read-only plotting commands over existing pipeline artifacts. QC reads the
explicit paths supplied on the command line, computes values for display (and,
for orientation scatter, an optional table), and writes new outputs. It never
mutates upstream artifacts, does not infer paths from `--project-dir`, and is
not a pass/warn/fail gate. A plot can reveal an unusual distribution or poor
concordance without causing the pipeline to accept or reject an assay.

```bash
yulab_reporter_qc --help
yulab_reporter_qc <subcommand> --help
```

| Subcommand | Typical input | Purpose |
| --- | --- | --- |
| `make_umi_per_elem_plot` | Step 5 [`crosswalk-map`](../formats.md#crosswalk-map) | Pre-transfection UMI depth per element |
| `make_ID_per_elem_plot` | `crosswalk-map` | Distinct barcode IDs per element |
| `make_umi_per_id_plot` | `crosswalk-map` | UMI support by crosswalk row or ID grouping |
| `make_between_rep_activity_plot` | Step 8 [`element-counts`](../formats.md#element-counts) | Between-replicate activity concordance |
| `plot_orientation_scatter` | Step 9 [`activity-by-element`](../formats.md#activity-by-element) + references | Forward-vs-reverse activity scatter |

## Shared figure options

Unless noted, subcommands accept:

| Flag | Default | Notes |
| --- | --- | --- |
| `--dpi` | `300` | |
| `--figure-width` | `4.0` | inches |
| `--figure-height` | `3.0` | inches |
| `--title` | auto | |
| `--output-path` | required | Plot destination; `.png` is the supported contract suffix |

---

## Pre-transfection plots

All three use one `--records` file conforming to [`crosswalk-map`](../formats.md#crosswalk-map)
(typically `work/id_map_generation/pretran_step5_id_crosswalk.tsv.gz`).

The suffix-fixed `crosswalk-map` header identifies its ID columns: every column
before `Element` and `PreTranUMICount` is an ID column. The standard dual-ID
profile is `EID`, `PID`, `Element`, `PreTranUMICount`; a single-ID profile may
have only `EID`, `Element`, `PreTranUMICount`. Values are calculated from valid
retained rows, not from raw reads.

### `make_umi_per_elem_plot`

| Flag | Required | Default |
| --- | --- | --- |
| `--records` | yes | — |
| `--output-path` | yes | — |
| `--plot-type` | no | `cdf` (`cdf` \| `cdf-count` \| `hist`) |

Counting grain is one value per `Element`: sum `PreTranUMICount` across all
crosswalk rows assigned to that element. `cdf` plots the sorted values against
cumulative fraction; `cdf-count` uses cumulative element count; `hist` uses
element count on the y-axis (the released renderer uses a log y-axis). All
three use a linear x-axis with lower limit 0 and include a legend identifying
the rendered CDF or histogram series. These are descriptive depth distributions,
not acceptance criteria.

### `make_ID_per_elem_plot`

| Flag | Required | Default |
| --- | --- | --- |
| `--records` | yes | — |
| `--output-path` | yes | — |
| `--id-column` | yes | Must be a leading ID column from the file header (for example `EID` or `PID`) |
| `--plot-type` | no | `cdf` (`cdf` \| `cdf-count` \| `hist`) |

Counting grain is one value per `Element`: count distinct values in the selected
leading ID column. `--id-column` is resolved against the loaded file header;
it must not be `Element` or `PreTranUMICount`, and ID names are not a
hard-coded global list. The CDF and histogram encodings are the same as the
UMI-per-element command, with the x-axis representing distinct-ID count; each
CDF, cumulative-count, and histogram output includes a legend identifying the
rendered series.

### `make_umi_per_id_plot`

| Flag | Required | Default |
| --- | --- | --- |
| `--records` | yes | — |
| `--output-path` | yes | — |
| `--count-grain` | yes | `crosswalk-row` \| `id-pair` |
| `--plot-type` | no | `cdf` (`cdf` \| `cdf-complement` \| `cdf-count` \| `hist`) |
| `--x-max` | no | — (`cdf-complement` defaults to 20 when omitted) |

With `crosswalk-row`, each retained row contributes its `PreTranUMICount`.
With `id-pair`, rows are grouped by the tuple of *all* leading ID columns and
their counts are summed; despite the historical name, this also works for a
single-ID profile. `cdf` and `cdf-count` show cumulative fraction or observation
count; `hist` shows observation count (log y-axis); `cdf-complement` shows
`1 - CDF` against the UMI cutoff and defaults to an x maximum of 20 unless
`--x-max` is supplied. Every CDF, complement-CDF, cumulative-count, and
histogram output includes a legend identifying its rendered series. All CDF
x-axes start at 0.

### Example

```bash
yulab_reporter_qc make_umi_per_elem_plot \
  --records work/id_map_generation/pretran_step5_id_crosswalk.tsv.gz \
  --plot-type cdf \
  --output-path "<out_dir>/qc/pretran_umi_per_element.png"

yulab_reporter_qc make_ID_per_elem_plot \
  --records work/id_map_generation/pretran_step5_id_crosswalk.tsv.gz \
  --id-column EID \
  --plot-type hist \
  --output-path "<out_dir>/qc/eid_per_element.png"

yulab_reporter_qc make_umi_per_id_plot \
  --records work/id_map_generation/pretran_step5_id_crosswalk.tsv.gz \
  --count-grain id-pair \
  --plot-type cdf-complement \
  --output-path "<out_dir>/qc/umi_per_id_pair.png"
```

---

## `make_between_rep_activity_plot`

Requires at least two DNA and two RNA [`element-counts`](../formats.md#element-counts)
tables for one branch. DNA and RNA path lists must have the same length.
Recomputes per-replicate `log2((RNA+pseudocount)/(DNA+pseudocount))` and plots
concordance (upper-triangle Pearson text, lower-triangle scatters).

| Flag | Required | Default |
| --- | --- | --- |
| `--dna-records` | yes | One or more paths per flag use |
| `--rna-records` | yes | Same count as DNA |
| `--output-path` | yes | — |
| `--pseudocount` | no | `1.0` |
| `--negative-control-annotation` | no | Optional highlighting |
| `--branch-label` | no | For example `eBC` or `pBC` |

No `--plot-type` for this command.

The command covers one branch (`eBC` or `pBC`) per invocation. Replicate lists
are paired by position (`DNA_i` with `RNA_i`), must have equal lengths, and
must contain at least two pairs. The analysis space is the intersection of
`Element` values present in every DNA and RNA `element-counts` table. For each
replicate and retained element it recomputes

```text
activity_i = log2((RNA_i + pseudocount) / (DNA_i + pseudocount))
```

using the supplied pseudocount (default `1.0`, never negative). The output is
an `R × R` grid whose figure dimensions scale by the per-panel
`--figure-width` and `--figure-height`: diagonal cells label the replicate;
upper-triangle cells show Pearson `r` for the pair; lower-triangle cells show
the corresponding scatter, with equal axes where feasible. If a
`negative-control-list` is supplied, matching elements are rendered as a
distinct series in lower-triangle panels. The plot is a concordance diagnostic;
the command does not define a correlation threshold or gate.

In a lower-triangle scatter panel, the legend identifies `Elements` and
`Negative controls` whenever both series are rendered. If only one series has
points, only that rendered series needs to appear in the legend.

```bash
yulab_reporter_qc make_between_rep_activity_plot \
  --dna-records work/posttran_element_mapping/eBC_DNA_rep1_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_DNA_rep2_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_DNA_rep3_step8_element_counts.tsv.gz \
  --rna-records work/posttran_element_mapping/eBC_RNA_rep1_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_RNA_rep2_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_RNA_rep3_step8_element_counts.tsv.gz \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --branch-label eBC \
  --output-path "<out_dir>/qc/ebc_between_replicates.png"
```

---

## `plot_orientation_scatter`

Forward-vs-reverse activity scatter from a single Step 9
[`activity-by-element`](../formats.md#activity-by-element) table plus paired
reference FASTAs. Pairing is **positional** by reference record order (see
[Workflow](../workflow.md)#forwardreverse-reference-pairing). Activity rows are
split by reference membership; an `Element` present in neither reference is a
hard failure.

Only pairs with activity on **both** orientations are plotted. One-sided pairs
are omitted from the scatter. Optional `--table-output-path` writes an
[`orientation-collapsed-activity`](../formats.md#orientation-collapsed-activity)
table with one row per reference pair. If zero both-orientation pairs exist:

- With `--table-output-path`: table-only success (no plot written)
- Without it: failure

| Flag | Required | Default |
| --- | --- | --- |
| `--activity-output` | yes | Step 9 table (format ID `activity-by-element`) |
| `--forward-reference` | yes | FASTA |
| `--reverse-reference` | yes | FASTA |
| `--output-path` | yes | Plot path (always required; unused only on table-only success when no Both pairs exist) |
| `--table-output-path` | no | Optional collapsed table (`.tsv` or `.tsv.gz`) |
| `--metric` | no | `activity_score` (`activity_score` \| `activityZ`) |
| `--negative-control-annotation` | no | Red-edge highlight when either orientation name is listed |

### Correlation annotations

Every orientation scatter panel annotates Pearson and Spearman `r` over **all
plotted points** (including negative-control points when present):

- Spearman `r` is Pearson correlation of midrank-transformed x and y (average ranks for ties).
- When fewer than two points are available, or either axis has zero variance after the relevant transform, the coefficient is undefined and rendered as `nan`.
- Labels appear in the upper-left of the axes at 6 pt, left- and top-aligned, as:
  - `Pearson r = {value:.3f}` or `Pearson r = nan`
  - `Spearman r = {value:.3f}` or `Spearman r = nan`

```bash
yulab_reporter_qc plot_orientation_scatter \
  --activity-output "<out_dir>/EID-ActivityByElement.tsv.gz" \
  --forward-reference "<ref_dir>/forward_elements.fa" \
  --reverse-reference "<ref_dir>/reverse_elements.fa" \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --metric activity_score \
  --output-path "<out_dir>/qc/ebc_orientation_scatter.png" \
  --table-output-path "<out_dir>/qc/ebc_orientation_collapsed.tsv.gz"
```

The same command can be run for the other released branch by supplying its
Step 9 output and the corresponding references, for example:

```bash
yulab_reporter_qc plot_orientation_scatter \
  --activity-output "<out_dir>/PID-ActivityByElement.tsv.gz" \
  --forward-reference "<ref_dir>/forward_elements.fa" \
  --reverse-reference "<ref_dir>/reverse_elements.fa" \
  --metric activityZ \
  --output-path "<out_dir>/qc/pbc_orientation_scatter.png"
```

### Orientation-collapsed table

`--table-output-path` writes exactly one row for each positional FASTA pair,
in ascending `PairIndex`. The 26 columns are documented in the
[`orientation-collapsed-activity` format](../formats.md#orientation-collapsed-activity).
`PairCoverage` is `Both`, `FwdOnly`, `RevOnly`, or `Neither`; `Plotted` is true
only for `Both`. Per-orientation fields are copied when present and blank when
absent. `IsNegativeControl` is true when either element is listed in the
optional annotation (or false for every row when no annotation is supplied).

For a `Both` row, collapsed DNA and RNA counts are the sums of the two
orientation counts; collapsed `ActivityScore`, `Log2FC`, and `ActivityZ` are
the arithmetic means of the two corresponding fields. `CollapsedActivityCall`
is `Active` if either orientation call is `Active`, otherwise `Inactive`.
`ActivityScoreDelta` and `ActivityZDelta` are reverse minus forward. For
`FwdOnly` or `RevOnly`, collapsed values use the one present row and deltas are
blank. For `Neither`, all collapsed and delta fields are blank. The table is
still a successful, useful output when no pairs are `Both`; in that case no
plot is written. Without `--table-output-path`, zero `Both` pairs is an error.

### Pairing, plotting, and correlation interpretation

Forward and reverse FASTA records are paired by position, not by matching
header text. The references must have equal record counts and unique headers
within each file. Activity rows are partitioned by membership in the two
reference sets; an element in neither set is a hard validation failure. A
one-sided pair is omitted from the scatter, not treated as a zero. The selected
`activity_score` or `activityZ` is used on both axes, a dashed `y = x` line is
drawn, and negative-control points get a red edge when either paired name is
listed.

Pearson and Spearman annotations are computed over all plotted points,
including negative controls. Spearman is Pearson correlation after average
(midrank) transformation for ties. Each coefficient is `nan` when fewer than
two points are available or its transformed axes have zero variance; this is a
mathematical undefined case, not a QC failure threshold.

## QC validation failures and recovery

QC commands fail non-zero before producing a plot when required paths are
missing/unreadable, headers do not conform to the required format, an input
has no valid rows, an enum or numeric option is invalid, or an output cannot be
written. Between-replicate QC additionally fails for mismatched DNA/RNA list
lengths, fewer than two replicate pairs, or an empty shared `Element` space.
Orientation scatter additionally validates unique, non-empty FASTA references
with equal record counts, rejects duplicate `Element` rows in the
`activity-by-element` input, rejects activity elements in neither reference,
rejects a supplied negative-control file with no usable IDs, and requires at
least one `Both` pair when no table output was requested.

For duplicate activity rows, return to the Step 9 producer, validate that its
`activity-by-element` output has one row per `Element`, and regenerate the
artifact before rerunning QC. For an empty negative-control annotation, fix the
list to contain at least one non-empty element ID (one ID per line), or omit
`--negative-control-annotation` when highlighting is not needed. These are
input-contract failures; QC does not guess which duplicate row or control ID
to use.

Recovery is to verify the producer stage and artifact format, inspect the
stage summary and retained file paths, correct the invocation or input, and
rerun the read-only QC command. QC does not repair, delete, or rewrite the
pipeline artifacts, and a nonzero skipped/omitted count by itself is not a
pass/fail decision. When a grouped command has removed an intermediate, rerun
that producer with its documented retention option (or use the retained final
artifact) before invoking QC.
