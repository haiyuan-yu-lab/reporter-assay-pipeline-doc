# `yulab_reporter_export`

ExogeneousSequences export after `call_activity`.

```bash
yulab_reporter_export --help
yulab_reporter_export ES --help
```

## `ES`

Exports a FASTA of selected reference records plus one or more row-aligned
stat `.npy` annotation tracks.

| Flag | Required | Notes |
| --- | --- | --- |
| `--activity-output` | yes | Step 9 [`activity-by-element`](../formats.md#activity-by-element) table (CLI flag name remains `--activity-output`) |
| `--reference` | yes (repeatable, ≥1) | Tested-library FASTA. Dual-orientation libraries typically pass forward then reverse; CW-only / single-orientation libraries pass one. |
| `--negative-control-annotation` | yes | Plain-text ID list; must be non-empty; listed IDs are always excluded |
| `--output-fasta` | yes | Destination FASTA |
| `--anno-track COLUMN OUTPUT_NPY_PATH` | yes (≥1) | Repeatable |

Legacy `--forward-reference` / `--reverse-reference` are **not** accepted.

Supported `--anno-track` column names (case-sensitive):

`ActivityScore`, `log2FC`, `ActivityZ`, `DNACount`, `RNACount`

### Selection rules

- Pass one or more `--reference` FASTA paths. Headers must be unique within each
  file and disjoint across files.
- Export order is CLI `--reference` order, then within each file FASTA record
  order (not SPEC-001 positional forward/reverse pairing).
- Only reference records with matching activity data and finite values for **all**
  requested annotation columns are exported.
- Reference records without activity rows are **silently skipped**.
- Negative-control IDs are **always excluded**, even when activity data exist.
- Hard-fail if any activity `Element` is in none of the reference sets.
- Hard-fail if zero exportable records remain.
- Each `.npy` has shape `(M, 1)` float64, row-aligned to the exported FASTA.

Compatible with `RGTools.ExogeneousSequences` / `load_region_anno_from_npy(..., anno_type="stat")`.

### Examples

Dual-orientation eBC branch:

```bash
yulab_reporter_export ES \
  --activity-output "<out_dir>/EID-ActivityByElement.tsv.gz" \
  --reference "<ref_dir>/forward_elements.fa" \
  --reference "<ref_dir>/reverse_elements.fa" \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --output-fasta "<out_dir>/es_export/EID_library.fa" \
  --anno-track ActivityScore "<out_dir>/es_export/ActivityScore.npy" \
  --anno-track log2FC "<out_dir>/es_export/log2FC.npy" \
  --anno-track ActivityZ "<out_dir>/es_export/ActivityZ.npy"
```

CW-only / single-reference eBC branch:

```bash
yulab_reporter_export ES \
  --activity-output "<out_dir>/EID-ActivityByElement.tsv.gz" \
  --reference "<ref_dir>/forward_elements.fa" \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --output-fasta "<out_dir>/es_export/EID_library.fa" \
  --anno-track ActivityScore "<out_dir>/es_export/ActivityScore.npy" \
  --anno-track log2FC "<out_dir>/es_export/log2FC.npy" \
  --anno-track ActivityZ "<out_dir>/es_export/ActivityZ.npy"
```

Run once per branch with the matching activity table.
