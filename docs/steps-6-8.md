# Steps 6–8: quantify PostTran replicates

This page is the canonical procedure for turning one PostTran Step 2 delimited
records file into one element-count table for release **0.1.0b3**. Repeat the
three-step handoff independently for every DNA and RNA replicate. The [Pipeline
CLI](cli/pipe.md) is the compact flag reference; [Artifact formats](formats.md)
defines the shared column contracts.

eBC and pBC are separate assay branches. Use the eBC/EID cluster reference for
eBC libraries and the pBC/PID cluster reference for pBC libraries; do not mix
references or selector columns.

## Prerequisites and branch handoffs

Complete Steps 1–2 for the selected PostTran library and complete the PreTran
map in [Steps 3–5](steps-3-5.md). The Step 2 file must be readable, tab
delimited, have a header and at least one row, and use one of these exact
branch layouts:

| Branch | Step 2 columns | Step 5 reference | Step 8 selectors |
| --- | --- | --- | --- |
| eBC | `UMI`, `EID` | `pretran_step5_EID_cluster_reference.tsv.gz` | `EID`, `MoleculeCount` |
| pBC | `UMI1`, `PID1`, `PID2`, `UMI2` | `pretran_step5_PID_cluster_reference.tsv.gz` | `PID1`, `MoleculeCount` |

If a replicate was parsed twice with orientation-specific layouts, concatenate
the compatible gzip-compressed Step 2 tables into the single path that
`process_posttrans` will resolve (`work/delimited/<library-prefix>_step2_records.tsv.gz`)
before this grouped command. See
[`concat_step2_records`](cli/pipe.md#concat_step2_records). Do not concatenate
Step 2 summary JSON files.

Each cluster reference is a `cluster-reference` table with
`ObservedID`, `CanonicalID`, and `Element`. Its observed IDs must be unique and
its IDs must be non-empty. The same reference is supplied to Step 6 for
observed-to-canonical matching and to Step 8 for canonical-ID-to-Element
mapping.

## Complete grouped commands

`process_posttrans` runs Steps 6, 7, and 8 in order. It resolves the Step 2
input as `work/delimited/<library-prefix>_step2_records.tsv.gz`, wires each
stage's output to the next stage, and retains final outputs and summaries. Use
`--no-delete-intermediate` while diagnosing so the Step 6 and Step 7 tables are
preserved.

For an eBC replicate:

```bash
yulab_reporter_pipe process_posttrans \
  --library-prefix eBC_DNA_rep1 \
  --id-field EID \
  --cluster-reference work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz \
  --input-id-col EID \
  --input-count-col MoleculeCount \
  --project-dir "<project_dir>" \
  --no-delete-intermediate
```

For a pBC replicate:

```bash
yulab_reporter_pipe process_posttrans \
  --library-prefix pBC_DNA_rep1 \
  --id-field PID1 \
  --cluster-reference work/id_map_generation/pretran_step5_PID_cluster_reference.tsv.gz \
  --input-id-col PID1 \
  --input-count-col MoleculeCount \
  --project-dir "<project_dir>" \
  --no-delete-intermediate
```

Replace `DNA` with `RNA` and `rep1` with each replicate number. Run once per
library; a failure for one replicate does not invalidate successful outputs
from other libraries. The grouped command's `--cluster-reference` is passed to
both Step 6 and Step 8 internally.

## Step 6: match observed IDs to canonical IDs

The individual form is useful for resuming or diagnosing a grouped run:

```bash
yulab_reporter_pipe step6 \
  --library-prefix eBC_DNA_rep1 \
  --id-field EID \
  --input-records work/delimited/eBC_DNA_rep1_step2_records.tsv.gz \
  --cluster-reference work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz \
  --project-dir "<project_dir>"
```

Use `--id-field EID` and the EID reference for eBC; use `--id-field PID1` and
the PID reference for pBC. Step 6 resolves the branch from the Step 2 schema:
exactly one supported layout must be present, a valid eBC layout (`UMI`,
`EID`) or a valid pBC layout (`UMI1`, `PID1`, `PID2`, `UMI2`). It then
validates the selected input column, the branch-required columns, and the
reference's `ObservedID`/`CanonicalID` columns and unique observed keys. It
performs an exact lookup of each observed value in `ObservedID` and emits the
corresponding `CanonicalID`. There is no fuzzy remapping.

Rows with missing required fields, malformed columns, an `N` in the selected
identifier, or no reference match are skipped and counted. These row-level
conditions are not fatal if at least one row remains. A missing/corrupt input
or reference, invalid configuration, duplicate observed key, ambiguous eBC/pBC
schema, unwritable output, or zero retained rows is fatal and produces a
failed summary; do not start Step 7 after such a failure.

Step 6 writes:

| Artifact | Contract |
| --- | --- |
| `work/posttran_id_matching/<prefix>_step6_matched_records.tsv.gz` | eBC: `EID`, `UMI`; pBC: `UMI1`, `PID1`, `PID2`, `UMI2`. The selected ID is canonicalized. |
| `work/posttran_id_matching/<prefix>_step6_summary.json` | Run metadata and row-level skip counts. |

The summary includes `library_prefix`, `branch`, `id_field`, input/reference
and output paths, `input_record_count`,
`output_record_count`, `skipped_missing_field_count`,
`skipped_invalid_row_count`, `skipped_contains_n_count`,
`skipped_unmatched_id_count`, `status`, and `failure_reason`.
Completion requires `status` `success`, a non-empty matched-records file, the
expected branch header, and internally consistent counts.

### Step 6 exact matching

In **0.1.0b3**, matching is exact `ObservedID` to `CanonicalID` lookup. The
command surface does not accept `--min-match-length`; do not supply it or treat
match length as a tuning control.

## Step 7: deduplicate molecules and quantify the replicate

```bash
yulab_reporter_pipe step7 \
  --library-prefix eBC_DNA_rep1 \
  --input-records work/posttran_id_matching/eBC_DNA_rep1_step6_matched_records.tsv.gz \
  --project-dir "<project_dir>"
```

Step 7 resolves the branch from the matched-records schema. Exactly one
supported layout must be present: a valid eBC layout (`EID`, `UMI`) or a valid
pBC layout (`UMI1`, `PID1`, `PID2`, `UMI2`). It skips malformed rows and rows
missing required values, then deduplicates molecules before counting:

| Branch | Molecule key | Quantification key |
| --- | --- | --- |
| eBC | `(EID, UMI)` | `EID` |
| pBC | `(PID1, PID2, UMI1, UMI2)` | `(PID1, PID2)` |

Duplicate molecule keys count once. Output rows are deterministic and counts
are positive integers. A schema that resolves to neither supported layout or
matches both layouts is a fatal, ambiguous-branch configuration error. A valid
single eBC or pBC layout is accepted. A corrupt input, unwritable output, or
zero retained molecules is also fatal; malformed rows alone are tolerated when
valid molecules remain.

Step 7 writes:

| Artifact | Contract |
| --- | --- |
| `work/posttran_quantification/<prefix>_step7_quantification.tsv.gz` | eBC: `EID`, `MoleculeCount`; pBC: `PID1`, `PID2`, `MoleculeCount`. |
| `work/posttran_quantification/<prefix>_step7_summary.json` | Includes `library_prefix`, `branch`, input/output paths, `input_record_count`, skip counts, `deduplicated_molecule_count`, `output_group_count`, `status`, and `failure_reason`. |

Completion requires a non-empty output with the branch-specific header and a
successful summary. Do not continue to Step 8 after a failed summary.

## Step 8: map canonical IDs to Elements

```bash
yulab_reporter_pipe step8 \
  --library-prefix eBC_DNA_rep1 \
  --input-records work/posttran_quantification/eBC_DNA_rep1_step7_quantification.tsv.gz \
  --element-reference work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz \
  --input-id-col EID \
  --input-count-col MoleculeCount \
  --project-dir "<project_dir>"
```

Use `PID1` and the PID reference for pBC. Step 8 validates the selected input
columns and the reference's `CanonicalID`/`Element` mapping. For each row it
performs an exact canonical-ID lookup; malformed rows, missing fields,
non-positive/non-integer counts, and unmapped canonical IDs are skipped and
counted. Retained counts are summed by `Element`. Duplicate canonical IDs in
the reference that map to different Elements are fatal, as are corrupt input,
unwritable output, and zero mapped rows.

Step 8 writes:

| Artifact | Contract |
| --- | --- |
| `work/posttran_element_mapping/<prefix>_step8_element_counts.tsv.gz` | Exactly `Element`, `MoleculeCount`, one deterministic row per Element. |
| `work/posttran_element_mapping/<prefix>_step8_summary.json` | Includes `library_prefix`, input/reference paths, selectors, input and skip counts, `skipped_unmapped_id_count`, `mapped_record_count`, `output_element_count`, `status`, and `failure_reason`. |

Completion requires a non-empty element-count table, positive integer counts,
and `status` `success`. These tables are the Step 9 DNA/RNA inputs.

## Validation and symptom-first recovery

Check summaries and required artifacts before advancing:

```bash
for stage in posttran_id_matching posttran_quantification posttran_element_mapping; do
  find "<project_dir>/work/${stage}" -name 'eBC_DNA_rep1_*summary.json' -print
done
jq '{status, failure_reason, input_record_count, output_record_count,
    skipped_missing_field_count, skipped_invalid_row_count,
    skipped_contains_n_count, skipped_unmatched_id_count}' \
  "<project_dir>/work/posttran_id_matching/eBC_DNA_rep1_step6_summary.json"
jq '{status, failure_reason, input_record_count, deduplicated_molecule_count,
    output_group_count}' \
  "<project_dir>/work/posttran_quantification/eBC_DNA_rep1_step7_summary.json"
jq '{status, failure_reason, input_record_count, mapped_record_count,
    skipped_unmapped_id_count, output_element_count}' \
  "<project_dir>/work/posttran_element_mapping/eBC_DNA_rep1_step8_summary.json"
```

| Symptom | Classification | Recovery |
| --- | --- | --- |
| Step 6 has many unmatched, `N`, or missing rows | Tolerated row loss or wrong branch/reference | Check the Step 2 header, `--id-field`, and matching EID/PID cluster reference; inspect summary counts, correct the input/reference, and rerun Step 6. |
| Step 6 summary is `failed` or matched output is empty | Fatal handoff failure | Fix the reported schema, reference, parsing, or output problem; rerun Step 6 before Step 7. |
| Step 6 or Step 7 reports ambiguous schema | Unsupported eBC/pBC-compatible input | Remove the extra branch columns so exactly one schema remains; rerun Step 6, then Step 7. |
| Step 7 has high deduplication or no groups | Valid duplicate collapse or fatal zero-output | Inspect molecule-key inputs and summary; continue only with `success` and groups > 0, otherwise repair and rerun Step 7. |
| Step 8 has unmapped IDs | Tolerated mapping loss or wrong domain | Use `EID` with the EID cluster reference for eBC, or `PID1` with the PID cluster reference for pBC; inspect canonical IDs and rerun Step 8 after correction. |
| Step 8 summary is `failed` or output is empty | Fatal mapping/output failure | Fix selectors, reference uniqueness, counts, or I/O; rerun Step 8 before Step 9. |
| Grouped run stops after Step 6 or 7 | Resumable orchestration failure | Preserve intermediates with `--no-delete-intermediate`, read the failed summary, and rerun the first failed individual step using the commands above. |

Never infer completion from a file's presence alone. A replicate is ready for
Step 9 only when all three summaries report `success`, the Step 8 table is
non-empty, and its header is exactly `Element\tMoleculeCount`.
