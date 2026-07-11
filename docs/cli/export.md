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
| `--forward-reference` | yes | Tested-library FASTA |
| `--reverse-reference` | yes | Tested-library FASTA (same record count; positional pairing) |
| `--negative-control-annotation` | yes | Plain-text ID list; must be non-empty; listed IDs are always excluded |
| `--output-fasta` | yes | Destination FASTA |
| `--anno-track COLUMN OUTPUT_NPY_PATH` | yes (≥1) | Repeatable |

Supported `--anno-track` column names (case-sensitive):

`ActivityScore`, `log2FC`, `ActivityZ`, `DNACount`, `RNACount`

### Selection rules

- Forward/reverse references must have equal record counts, unique headers within each file, and disjoint header sets between files.
- Only reference records with matching activity data and finite values for **all** requested annotation columns are exported.
- Reference records without activity rows are **silently skipped**.
- Negative-control IDs are **always excluded**, even when activity data exist.
- Hard-fail if any activity `Element` is in neither reference set.
- Hard-fail if zero exportable records remain.
- Export order is deterministic: scan pair index `i`, emit forward then reverse when each side is selected.
- Each `.npy` has shape `(M, 1)` float64, row-aligned to the exported FASTA (`0 < M ≤ 2N`).

Compatible with `RGTools.ExogeneousSequences` / `load_region_anno_from_npy(..., anno_type="stat")`.

### Example

```bash
yulab_reporter_export ES \
  --activity-output "<out_dir>/EID-ActivityByElement.tsv.gz" \
  --forward-reference "<ref_dir>/forward_elements.fa" \
  --reverse-reference "<ref_dir>/reverse_elements.fa" \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --output-fasta "<out_dir>/es_export/EID_library.fa" \
  --anno-track ActivityScore "<out_dir>/es_export/ActivityScore.npy" \
  --anno-track log2FC "<out_dir>/es_export/log2FC.npy" \
  --anno-track ActivityZ "<out_dir>/es_export/ActivityZ.npy"
```

Run once per branch (eBC / pBC) with the matching activity table.
