# `yulab_reporter_pipe`

Pipeline steps and grouped workflows.

The released documentation is the behavioral contract for **0.1.0b2**. The
installed command's help describes the local build and may be incomplete for
individual steps. See [Known limitations](../known-limitations.md), including
the ineffective Step 6 `--min-match-length` option and inconsistent ambiguous
branch handling.

For the complete post-transfection procedure, branch handoffs, artifact
contracts, and recovery guidance, see [Steps 6–8](../steps-6-8.md).
For the activity formulas, summary schema, and Step 9 recovery matrix, see
[Step 9: call activity](../steps-9.md).

```bash
yulab_reporter_pipe --help
yulab_reporter_pipe <subcommand> --help
```

| Command | Steps | Purpose |
| --- | --- | --- |
| `step1` … `step9` | one each | Individual stages |
| `prep_lib` | 1 → 2 | Trim + delimited records |
| `process_pretrans` | 3 → 4 → 5 | Dual-orientation PreTran (CW + CCW) + ID maps |
| `process_pretrans_cw_only` | 3 → 4 → 5 | CW-only PreTran + ID maps |
| `process_posttrans` | 6 → 7 → 8 | One post-transfection replicate |
| `call_activity` | 9 | Activity calling |

Grouped commands wire step-to-step intermediates automatically. By default,
`--delete-intermediate` is **on**: orchestrator-managed intermediates are
removed after a successful run while final outputs and `*_summary.json` files
are retained. Pass `--no-delete-intermediate` to keep intermediates.

Shared optional flags on grouped commands: `--project-dir` (default: cwd),
`--output-dir` (defaults under `work/` as described in [Workflow](../workflow.md)).

PreTran ID profile is **CLI-declared** via required `--id-columns` (for
example `EID,PID` or `EID`). Step 5 emits one cluster-reference file per
declared ID using ExactID filenames
(`pretran_step5_EID_cluster_reference.tsv.gz`, etc.).

---

## Grouped commands

### `prep_lib` (step1 → step2)

**Required:** `--library-prefix`, `--input-r1`, `--input-r2`, `--layout-schema`

**Optional:** `--project-dir`, `--output-dir`, `--threads` (default `16`), `--cleaner` (default `fastp`), `--max-edit-distance` (default `1`), `--min-last-anchor-match` (default `10`), `--delete-intermediate` / `--no-delete-intermediate`

**Retained outputs (typical):** `{prefix}_step2_records.tsv.gz` under `work/delimited/`, plus Step 1/2 summary JSON files.

Step 2 inputs are wired from Step 1 cleaned reads.

### `process_pretrans` (step3 CW → step3 CCW → step4 → step5)

**Required:** `--id-columns`, `--cw-prefix`, `--ccw-prefix`, `--cw-records`, `--ccw-records`, `--forward-reference`, `--reverse-reference`

**Optional:** `--project-dir`, `--output-dir`, `--max-edit-distance` (default `1`), `--min-pretran-umi-count` (default `1`), `--cluster-mode` (`connected` \| `unique`, default `connected`), `--cluster-max-edit-distance` (default `1`), `--idmap-min-dominant-count` (default `10`), `--idmap-min-dominant-ratio` (default `0.8`), `--delete-intermediate` / `--no-delete-intermediate`

**Retained outputs (typical, dual-ID):**

- `work/id_map_generation/pretran_step5_id_crosswalk.tsv.gz`
- `work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz`
- `work/id_map_generation/pretran_step5_PID_cluster_reference.tsv.gz`
- Step summaries

### `process_pretrans_cw_only` (step3 CW → step4 → step5)

CW-only PreTran path. Omits the CCW trio; Step 4 receives a single Step 3
output via `--records`.

**Required:** `--id-columns`, `--cw-prefix`, `--cw-records`, `--forward-reference`

**Rejected:** `--ccw-prefix`, `--ccw-records`, `--reverse-reference`

**Optional:** same Step 5 / project / intermediate flags as `process_pretrans`

**Retained outputs (typical, EID-only):**

- `work/id_map_generation/pretran_step5_id_crosswalk.tsv.gz`
- `work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz`
- Step summaries

### `process_posttrans` (step6 → step7 → step8)

**Required:** `--library-prefix`, `--id-field`, `--cluster-reference`, `--input-id-col`, `--input-count-col`

**Optional:** `--project-dir`, `--output-dir`, `--min-match-length` (default `20`), `--delete-intermediate` / `--no-delete-intermediate`

**Input resolution:** Step 6 `--input-records` is resolved automatically as
`<project-dir>/work/delimited/<library-prefix>_step2_records.tsv.gz`. Run
`prep_lib` for that prefix first (or place an equivalent Step 2 file at that path).

`--cluster-reference` is used for Step 6 matching and is also passed to Step 8
as the element reference.

**Retained output (typical):** `work/posttran_element_mapping/<prefix>_step8_element_counts.tsv.gz` plus step summaries.

### `call_activity` (step9)

**Required:** `--dna-records` (repeatable; one or more paths per use), `--rna-records` (same count as DNA), `--negative-control-annotation`, `--output-path`

**Optional:** `--project-dir`, `--summary-path` (derived from `--output-path` when omitted), `--pseudocount` (default `1.0`), `--activity-threshold-z` (default `2.0`), `--delete-intermediate` / `--no-delete-intermediate` (no-op; no orchestrator intermediates)

DNA and RNA lists must contain the same number of replicate tables. Run once per
branch (eBC and pBC when both are present). Output format: [`activity-by-element`](../formats.md#activity-by-element).

---

## End-to-end example

Replace angle-bracket placeholders with local paths. Example uses three
replicates per branch/material.

### 1. Prepare libraries

```bash
for prefix in PreTran_CW PreTran_CCW; do
  yulab_reporter_pipe prep_lib \
    --library-prefix "${prefix}" \
    --input-r1 "<raw_dir>/${prefix}_R1.fastq.gz" \
    --input-r2 "<raw_dir>/${prefix}_R2.fastq.gz" \
    --layout-schema "<schemas>/pretran_layout.json"
done

for branch in eBC pBC; do
  for material in DNA RNA; do
    for rep in 1 2 3; do
      prefix="${branch}_${material}_rep${rep}"
      yulab_reporter_pipe prep_lib \
        --library-prefix "${prefix}" \
        --input-r1 "<raw_dir>/${prefix}_R1.fastq.gz" \
        --input-r2 "<raw_dir>/${prefix}_R2.fastq.gz" \
        --layout-schema "<schemas>/${branch,,}_layout.json"
    done
  done
done
```

### 2. Process pre-transfection

Dual-orientation + dual-ID:

```bash
yulab_reporter_pipe process_pretrans \
  --id-columns EID,PID \
  --cw-prefix PreTran_CW \
  --ccw-prefix PreTran_CCW \
  --cw-records work/delimited/PreTran_CW_step2_records.tsv.gz \
  --ccw-records work/delimited/PreTran_CCW_step2_records.tsv.gz \
  --forward-reference "<ref_dir>/forward_elements.fa" \
  --reverse-reference "<ref_dir>/reverse_elements.fa"
```

CW-only / EID-only alternative:

```bash
yulab_reporter_pipe process_pretrans_cw_only \
  --id-columns EID \
  --cw-prefix PreTran_CW \
  --cw-records work/delimited/PreTran_CW_step2_records.tsv.gz \
  --forward-reference "<ref_dir>/forward_elements.fa"
```

### 3. Process post-transfection replicates

```bash
for material in DNA RNA; do
  for rep in 1 2 3; do
    prefix="eBC_${material}_rep${rep}"
    yulab_reporter_pipe process_posttrans \
      --library-prefix "${prefix}" \
      --id-field EID \
      --cluster-reference work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz \
      --input-id-col EID \
      --input-count-col MoleculeCount
  done
done

for material in DNA RNA; do
  for rep in 1 2 3; do
    prefix="pBC_${material}_rep${rep}"
    yulab_reporter_pipe process_posttrans \
      --library-prefix "${prefix}" \
      --id-field PID1 \
      --cluster-reference work/id_map_generation/pretran_step5_PID_cluster_reference.tsv.gz \
      --input-id-col PID1 \
      --input-count-col MoleculeCount
  done
done
```

### 4. Call activity

```bash
yulab_reporter_pipe call_activity \
  --dna-records work/posttran_element_mapping/eBC_DNA_rep1_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_DNA_rep2_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_DNA_rep3_step8_element_counts.tsv.gz \
  --rna-records work/posttran_element_mapping/eBC_RNA_rep1_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_RNA_rep2_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/eBC_RNA_rep3_step8_element_counts.tsv.gz \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --output-path "<out_dir>/EID-ActivityByElement.tsv.gz"

yulab_reporter_pipe call_activity \
  --dna-records work/posttran_element_mapping/pBC_DNA_rep1_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/pBC_DNA_rep2_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/pBC_DNA_rep3_step8_element_counts.tsv.gz \
  --rna-records work/posttran_element_mapping/pBC_RNA_rep1_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/pBC_RNA_rep2_step8_element_counts.tsv.gz \
               work/posttran_element_mapping/pBC_RNA_rep3_step8_element_counts.tsv.gz \
  --negative-control-annotation "<ref_dir>/negative_controls.txt" \
  --output-path "<out_dir>/PID-ActivityByElement.tsv.gz"
```

---

## Individual step flags

Use individual steps for debugging or resumable runs when intermediates already
exist. All steps accept `--project-dir` (default cwd) and usually `--output-dir`
(default under `work/`). Grouped-command `--help` is the richest surface for
orchestrated flags; step modules also expose their own parsers.

### `step1`

| Flag | Required | Default |
| --- | --- | --- |
| `--library-prefix` | yes | — |
| `--input-r1` | yes | — |
| `--input-r2` | yes | — |
| `--threads` | no | `16` |
| `--cleaner` | no | `fastp` |

### `step2`

| Flag | Required | Default |
| --- | --- | --- |
| `--library-prefix` | yes | — |
| `--input-r1` | yes | — |
| `--input-r2` | yes | — |
| `--layout-schema` | yes | — |
| `--threads` | no | `16` |
| `--max-edit-distance` | no | `1` |
| `--min-last-anchor-match` | no | `10` |

### `step3`

| Flag | Required | Default |
| --- | --- | --- |
| `--library-prefix` | yes | — |
| `--input-records` | yes | — |
| `--reference` | yes | Orientation-appropriate FASTA |
| `--id-columns` | yes | e.g. `EID,PID` or `EID` |
| `--max-edit-distance` | no | `1` |

### `step4`

| Flag | Required | Default |
| --- | --- | --- |
| `--records` | yes (repeatable, ≥1) | — |
| `--id-columns` | yes | Must match Step 3 / Step 5 |

### `step5`

| Flag | Required | Default |
| --- | --- | --- |
| `--pretran-counts` | yes | — |
| `--id-columns` | yes | Declares cluster domains |
| `--min-pretran-umi-count` | no | `1` |
| `--cluster-mode` | no | `connected` |
| `--cluster-max-edit-distance` | no | `1` |
| `--idmap-min-dominant-count` | no | `10` |
| `--idmap-min-dominant-ratio` | no | `0.8` |

### `step6`

| Flag | Required | Default |
| --- | --- | --- |
| `--library-prefix` | yes | — |
| `--id-field` | yes | — |
| `--input-records` | yes | — |
| `--cluster-reference` | yes | — |
| `--min-match-length` | no | `20` |

### `step7`

| Flag | Required | Default |
| --- | --- | --- |
| `--library-prefix` | yes | — |
| `--input-records` | yes | — |

### `step8`

| Flag | Required | Default |
| --- | --- | --- |
| `--library-prefix` | yes | — |
| `--input-records` | yes | — |
| `--element-reference` | yes | — |
| `--input-id-col` | yes | — |
| `--input-count-col` | yes | — |

### `step9`

| Flag | Required | Default |
| --- | --- | --- |
| `--dna-records` | yes | — |
| `--rna-records` | yes | — |
| `--negative-control-annotation` | yes | — |
| `--output-path` | yes | — |
| `--summary-path` | no | derived from `--output-path` |
| `--pseudocount` | no | `1.0` |
| `--activity-threshold-z` | no | `2.0` |

Step 9 output columns: `Element`, `DNACount`, `RNACount`, `ActivityScore`,
`log2FC`, `ActivityZ`, `ActivityCall` ([`activity-by-element`](../formats.md#activity-by-element)).
