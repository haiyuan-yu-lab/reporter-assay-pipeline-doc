# `yulab_reporter_qc`

Read-only plotting commands over existing pipeline artifacts. QC never mutates
upstream files and does not infer inputs from `--project-dir` — pass explicit
paths. There is no pass/warn/fail gating in v1.

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

### `make_umi_per_elem_plot`

| Flag | Required | Default |
| --- | --- | --- |
| `--records` | yes | — |
| `--output-path` | yes | — |
| `--plot-type` | no | `cdf` (`cdf` \| `cdf-count` \| `hist`) |

### `make_ID_per_elem_plot`

| Flag | Required | Default |
| --- | --- | --- |
| `--records` | yes | — |
| `--output-path` | yes | — |
| `--id-column` | yes | Must be a leading ID column from the file header (for example `EID` or `PID`) |
| `--plot-type` | no | `cdf` (`cdf` \| `cdf-count` \| `hist`) |

### `make_umi_per_id_plot`

| Flag | Required | Default |
| --- | --- | --- |
| `--records` | yes | — |
| `--output-path` | yes | — |
| `--count-grain` | yes | `crosswalk-row` \| `id-pair` |
| `--plot-type` | no | `cdf` (`cdf` \| `cdf-complement` \| `cdf-count` \| `hist`) |
| `--x-max` | no | — (`cdf-complement` defaults to 20 when omitted) |

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
