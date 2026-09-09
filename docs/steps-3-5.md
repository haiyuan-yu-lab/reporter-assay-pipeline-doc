# Steps 3–5: build the PreTran identifier map

This page is the canonical procedure for running and checking Steps 3–5 for
release **0.1.0b2**. Use it when you need explicit handoffs, resumable
execution, or diagnosis of PreTran mapping. The [Pipeline CLI](cli/pipe.md)
is the compact flag reference; [Artifact formats](formats.md) is the
canonical column reference.

## What the handoff does

Steps 3–5 turn Step 2 PreTran records into artifacts used by post-transfection
matching:

1. Step 3 assigns each PreTran anchor to a tested-library `Element` using the
   orientation-specific FASTA.
2. Step 4 merges one or more orientation-resolved tables, deduplicates UMI
   molecules across inputs, resolves ambiguous UMI assignments, and counts
   molecules per declared identifier tuple and `Element`.
3. Step 5 filters weak counts, clusters sequencing variants independently in
   each declared identifier domain, removes ambiguous or inconsistent mappings,
   and emits a crosswalk plus one cluster reference per declared ID.

The terms are deliberately distinct: `EID` and `PID` are identifier domains;
eBC and pBC are assay branches; `Element` is the tested-library element;
`ObservedID` is a value seen in PreTran or post-transfection data; and
`CanonicalID` is the representative used for downstream matching. An
`ExactID` in an output filename is the exact identifier-column name declared
with `--id-columns` (for example, `EID` or `PID`), not a new identifier value.

## Prerequisites

Complete [Steps 1–2](steps-1-2.md) for every required PreTran orientation.
Each Step 2 records file must be readable, non-empty, and have exactly the
declared ID columns plus `UMI` and `ElementAnchorSeq`. Prepare the tested-library
FASTA references as described in [Prepare inputs](input-preparation.md):
headers are unique `Element` names and sequences are the orientation-specific
reference payloads.

Use one ordered `--id-columns` value throughout the run. The dual-ID profile
uses `EID,PID`; an EID-only profile uses `EID`. The same value must match every
Step 3/4/5 schema, including spelling and order.

For a dual-orientation run, the caller is responsible for supplying a valid
forward/reverse FASTA pair: both files must have the same record count, and
record *i* in each file must represent the same physical element in opposite
orientations. Step 3 receives one orientation-specific reference at a time and
does not validate this positional pairing. Perform the [reference FASTA
checks](input-preparation.md#reference-fasta-checks) before running; the same
equal-count/order invariant is enforced for orientation-scatter QC in
[`plot_orientation_scatter`](cli/qc.md#plot_orientation_scatter). Use
`PreTran_CW` with the forward reference and `PreTran_CCW` with the reverse
reference. For CW-only operation, omit the CCW library and reverse reference
entirely.

## Complete grouped command

The grouped command runs Step 3 CW, Step 3 CCW, Step 4, then Step 5. The
`--cw-records` and `--ccw-records` paths are Step 2 inputs; the orchestrator
then wires the two newly produced orientation-resolved outputs into Step 4.

```bash
yulab_reporter_pipe process_pretrans \
  --id-columns EID,PID \
  --cw-prefix PreTran_CW \
  --ccw-prefix PreTran_CCW \
  --cw-records "<project_dir>/work/delimited/PreTran_CW_step2_records.tsv.gz" \
  --ccw-records "<project_dir>/work/delimited/PreTran_CCW_step2_records.tsv.gz" \
  --forward-reference "<reference_dir>/elements_forward.fa" \
  --reverse-reference "<reference_dir>/elements_reverse.fa" \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work" \
  --max-edit-distance 1 \
  --min-pretran-umi-count 1 \
  --cluster-mode connected \
  --cluster-max-edit-distance 1 \
  --idmap-min-dominant-count 10 \
  --idmap-min-dominant-ratio 0.8 \
  --no-delete-intermediate
```

The default is `--delete-intermediate`: after all four invocations succeed,
the orchestrator may remove Step 3 records, Step 4 merged counts, and other
listed intermediates. It never removes final Step 5 outputs or summaries. Use
`--no-delete-intermediate` while diagnosing or when you need to inspect a
downstream handoff.

For a CW-only/EID-only run, use the separate command:

```bash
yulab_reporter_pipe process_pretrans_cw_only \
  --id-columns EID \
  --cw-prefix PreTran_CW \
  --cw-records "<project_dir>/work/delimited/PreTran_CW_step2_records.tsv.gz" \
  --forward-reference "<reference_dir>/elements_forward.fa" \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work" \
  --cluster-mode connected \
  --cluster-max-edit-distance 1 \
  --idmap-min-dominant-count 10 \
  --idmap-min-dominant-ratio 0.8 \
  --no-delete-intermediate
```

Do not pass CCW flags to `process_pretrans_cw_only`; they are rejected. A
CW-only run emits only the EID cluster reference when `--id-columns EID`.

## Individual commands and handoffs

Run these commands when resuming after a completed stage or when the grouped
command has stopped. The paths below use explicit output roots so each handoff
is visible.

### Step 3: orientation matching

Run once per present orientation. The `--reference` is selected by the caller;
it is not inferred from the prefix.

```bash
yulab_reporter_pipe step3 \
  --library-prefix PreTran_CW \
  --input-records "<project_dir>/work/delimited/PreTran_CW_step2_records.tsv.gz" \
  --reference "<reference_dir>/elements_forward.fa" \
  --id-columns EID,PID \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work/pretran_orientation" \
  --max-edit-distance 1

yulab_reporter_pipe step3 \
  --library-prefix PreTran_CCW \
  --input-records "<project_dir>/work/delimited/PreTran_CCW_step2_records.tsv.gz" \
  --reference "<reference_dir>/elements_reverse.fa" \
  --id-columns EID,PID \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work/pretran_orientation" \
  --max-edit-distance 1
```

For each valid row, matching is attempted in this order: exact anchor, unique
exact containment of the anchor in a reference sequence, then bounded
edit-distance alignment when `--max-edit-distance` is greater than zero.
The edit-distance fallback uses the released `edlib`-backed contract: the
anchor is the query, the reference sequence is the target, and semi-global
(`HW`) alignment may find the anchor over any target interval while allowing
substitutions, insertions, and deletions up to the configured bound. Candidates
are compared at their minimum observed distance; a tie among distinct Elements
is ambiguous. Exact or containment matches are also ambiguous when more than
one distinct Element matches. Matching is against the single supplied
orientation reference, so CW and CCW must not share a reference accidentally.

Missing `UMI`, any declared ID, or `ElementAnchorSeq`; unmatched anchors; and
ambiguous matches are tolerated row-level skips and are counted. They do not
make the invocation fail if at least one row remains. The output header is
exactly `<id-columns in CLI order>, Element, UMI`.

Step 3 writes, under `work/pretran_orientation/`:

| Artifact | Meaning |
| --- | --- |
| `<prefix>_step3_orientation_resolved.tsv.gz` | `orientation-resolved-pretran` rows consumed by Step 4 |
| `<prefix>_step3_summary.json` | Counts, matching configuration, status, and failure reason |

The summary includes `library_prefix`, `id_columns`, `input_records_path`,
`reference_path`, `max_edit_distance`, `output_records_path`,
`input_record_count`, `output_record_count`,
`skipped_missing_field_count`, `skipped_unmatched_anchor_count`,
`skipped_ambiguous_match_count`, `status`, and `failure_reason`.

Completion requires `status` `success`, a non-empty output, the expected
header, and `output_record_count > 0`. A missing or malformed input/reference,
invalid configuration, unreadable output, or zero retained rows is fatal.

Check both orientations before Step 4:

```bash
for prefix in PreTran_CW PreTran_CCW; do
  test -s "<project_dir>/work/pretran_orientation/${prefix}_step3_orientation_resolved.tsv.gz"
  jq '{status, input_record_count, output_record_count,
       skipped_missing_field_count, skipped_unmatched_anchor_count,
       skipped_ambiguous_match_count, failure_reason}' \
    "<project_dir>/work/pretran_orientation/${prefix}_step3_summary.json"
done
```

### Step 4: merge and aggregate UMI counts

Step 4 accepts one or more orientation-resolved inputs. It does not inspect
filenames to decide orientation; CLI order is the deterministic merge order.
Identical molecules seen in CW and CCW (or in repeated inputs) are counted
once using `(<declared IDs...>, UMI)` as the deduplication key.

```bash
yulab_reporter_pipe step4 \
  --records "<project_dir>/work/pretran_orientation/PreTran_CW_step3_orientation_resolved.tsv.gz" \
  --records "<project_dir>/work/pretran_orientation/PreTran_CCW_step3_orientation_resolved.tsv.gz" \
  --id-columns EID,PID \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work/pretran_merge_counts"
```

Rows missing any required ID, `Element`, or `UMI` are skipped and counted.
After cross-input deduplication, a UMI assigned to multiple distinct ID tuples
is ambiguous. Step 4 retains the most frequent tuple for that UMI and drops
the others; equal-frequency ties choose the lexicographically smallest tuple
in declared ID order. Counts are then aggregated by
`(<declared IDs...>, Element)`.

The output header is exactly `<id-columns in CLI order>, Element,
PreTranUMICount`, with positive counts:

| Artifact | Meaning |
| --- | --- |
| `pretran_step4_merged_counts.tsv.gz` | `pretran-merged-counts` consumed by Step 5 |
| `pretran_step4_summary.json` | Input, deduplication, ambiguity, output, status, and failure reason |

The summary fields are `records_paths`, `id_columns`, `input_record_counts`,
`output_records_path`, `input_total_record_count`,
`skipped_missing_field_count`, `ambiguous_umi_count`,
`deduplicated_record_count`, `output_group_count`, `status`, and
`failure_reason`. `ambiguous_umi_count` counts unique UMIs requiring tuple
resolution, not the number of discarded rows.

Completion requires every input schema to match exactly, a non-empty merged
output, and `status` `success`. Missing inputs, schema mismatch, corrupt input,
unwritable output, or zero retained records is fatal. Malformed rows and
ambiguous UMIs alone are not fatal.

### Step 5: filter, cluster, and emit references

```bash
yulab_reporter_pipe step5 \
  --pretran-counts "<project_dir>/work/pretran_merge_counts/pretran_step4_merged_counts.tsv.gz" \
  --id-columns EID,PID \
  --project-dir "<project_dir>" \
  --output-dir "<project_dir>/work/id_map_generation" \
  --min-pretran-umi-count 1 \
  --cluster-mode connected \
  --cluster-max-edit-distance 1 \
  --idmap-min-dominant-count 10 \
  --idmap-min-dominant-ratio 0.8
```

Rows below `--min-pretran-umi-count` are filtered before clustering. Each
declared ID domain is clustered independently. `unique` leaves every observed
ID as its own canonical ID; `connected` joins IDs whose edit distance is at
most `--cluster-max-edit-distance`, using connected components. The canonical
member is the ID with highest aggregate `PreTranUMICount`, with a
lexicographically smallest-ID tie-break. `cluster-max-edit-distance 0` is
equivalent to `unique`.

For each canonical ID (and the full canonical tuple in a multi-ID profile),
Step 5 keeps only dominant mappings meeting both
`--idmap-min-dominant-count` and `--idmap-min-dominant-ratio` (dominant count
divided by total count). It then applies consistency checks after clustering:
conflicting canonical-ID-to-Element assignments are removed in every declared
direction, including the full canonical tuple-to-Element direction. An Element
having multiple canonical IDs is not itself a conflict. If no rows remain,
the invocation fails.

Step 5 writes:

| Artifact | Meaning |
| --- | --- |
| `pretran_step5_id_crosswalk.tsv.gz` | `crosswalk-map`: retained declared IDs, Element, and PreTranUMICount |
| `pretran_step5_EID_cluster_reference.tsv.gz` | EID `ObservedID` → `CanonicalID` → `Element` assignments |
| `pretran_step5_PID_cluster_reference.tsv.gz` | PID assignments when PID is declared |
| `pretran_step5_summary.json` | Filtering, clustering, conflict, output, status, and failure reason |

One cluster-reference file is emitted for each declared ID, with ExactID
casing. Every retained observed ID in a domain is assigned exactly once in its
domain reference. Cluster references are the downstream consumer for Step 6;
the crosswalk is the retained PreTran evidence and input to pre-trans QC,
including `pretrans_nc_representation` when you need to compare retained
negative controls with other elements before PostTran data exists (see
[`yulab_reporter_qc pretrans_nc_representation`](cli/qc.md#pretrans_nc_representation)).

The summary includes `input_pretran_counts_path`, `id_columns`,
`output_crosswalk_path`, `output_cluster_paths`, all clustering and threshold
options, `input_record_count`, `retained_record_count`,
`consistency_conflict_drop_count`,
`consistency_conflict_counts_by_direction`,
`skipped_missing_field_count`, `skipped_invalid_count_type_count`,
`distinct_id_counts`, `cluster_counts`, `status`, and `failure_reason`.

Completion requires a non-empty crosswalk, a non-empty cluster reference for
each declared ID, complete observed-ID assignments, internally consistent
summary metrics, and `status` `success`. Invalid configuration, schema/type
failure, corrupt input, unwritable output, or zero rows after filtering,
disambiguation, or consistency removal is fatal. A non-zero conflict count is
allowed when at least one valid row remains.

## Symptom-first recovery

| Symptom or summary evidence | Classification | Safe next action |
| --- | --- | --- |
| Step 3 has many `skipped_unmatched_anchor_count` rows | Tolerated row loss; possibly wrong reference/layout | Confirm CW uses forward and CCW uses reverse, inspect anchor extraction and FASTA sequences, then rerun only the affected Step 3 |
| Step 3 has `skipped_ambiguous_match_count` rows | Tolerated ambiguity | Make reference sequences/anchors uniquely resolvable; do not guess an Element; rerun the affected orientation |
| Step 3 output is empty or summary is `failed` | Fatal zero-output/configuration failure | Correct IDs, schema, reference, or edit-distance settings; rerun Step 3 before Step 4 |
| Step 4 `ambiguous_umi_count` is non-zero but status is `success` | Deterministically resolved ambiguity | Inspect the metric and input duplication; continue if the retained tuple assignments are acceptable |
| Step 4 schemas disagree or `output_group_count` is zero | Fatal handoff/zero-output failure | Verify every Step 3 header uses the same ordered IDs and has retained rows; rerun affected Step 3 files, then Step 4 |
| Step 5 has large count-filter or dominant-ratio loss | Valid but weak/ambiguous PreTran evidence | Review `min-pretran-umi-count`, dominant thresholds, and library depth; adjust only with an explicit analysis decision, then rerun Step 5 |
| Step 5 has consistency conflicts but retains rows | Tolerated mapping conflicts | Inspect `consistency_conflict_counts_by_direction`; use only the emitted crosswalk/references and record the loss |
| Step 5 removes all rows or a cluster reference is empty | Fatal map-generation failure | Correct PreTran inputs or thresholds and rerun Step 4/5 as appropriate; do not start Step 6 |
| Grouped run stopped after a completed stage | Resumable orchestration failure | Read the stage summary, preserve intermediates with `--no-delete-intermediate`, and rerun the first failed stage using the explicit commands above |

Never infer completion from the presence of one file. A PreTran map is ready
for Step 6 only when every required Step 3/4/5 summary reports `success`, the
crosswalk and each declared cluster reference are non-empty, and their headers
match the declared ID profile. Continue to [post-transfection Steps 6–8](cli/pipe.md)
with the exact cluster reference for the branch: EID for eBC and PID for pBC.
