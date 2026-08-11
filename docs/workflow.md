# Workflow

This page documents the released **0.1.0b2** stage graph, handoffs, and
retention behavior.

The pipeline starts from raw FASTQ pairs for pre-transfection and
post-transfection libraries. It trims and parses reads, builds pre-transfection
ID maps, matches post-transfection barcode observations back to those maps,
aggregates element counts, and calls activity from RNA/DNA signal.

Read-only QC plots and ExogeneousSequences export consume pipeline outputs; they
do not modify upstream artifacts.

## Diagram

```mermaid
flowchart TD
    RAW[Raw FASTQ pairs] --> S1[Step 1: Raw read preparation]
    S1 --> S2[Step 2: Delimited records]

    S2 -->|PreTran CW[/CCW]| S3[Step 3: Orientation]
    REF[Reference FASTA(s)] --> S3
    S3 --> S4[Step 4: Merge counts]
    S4 --> S5[Step 5: ID maps]

    S2 -->|PostTran records| S6[Step 6: ID matching]
    S5 -->|Cluster references| S6
    S6 --> S7[Step 7: Quantification]
    S7 --> S8[Step 8: Element mapping]

    S8 --> S9[Step 9: Activity calling]
    NEG[Negative controls] --> S9
    S9 --> ACT[Activity-by-element outputs]
    ACT --> QC[QC plots]
    ACT --> ES[ExogeneousSequences export]
```

## Stages and default paths

Default work directories sit under `<project-dir>/work/` (cwd when `--project-dir` is omitted).

| Stage | Input | Main output |
| --- | --- | --- |
| 1 | Raw R1/R2 FASTQ | Trimmed FASTQ under `work/trimmed/` |
| 2 | Trimmed FASTQ + layout schema | `work/delimited/<prefix>_step2_records.tsv.gz` |
| 3 | Step 2 records + one `--reference` | Orientation-resolved records under `work/pretran_orientation/` |
| 4 | One or more Step 3 outputs (`--records`) | Pre-transfection merged counts under `work/pretran_merge_counts/` |
| 5 | Step 4 counts + `--id-columns` | Crosswalk and per-ID cluster references under `work/id_map_generation/` |
| 6 | Post-transfection Step 2 records + cluster reference | Matched records under `work/posttran_id_matching/` |
| 7 | Step 6 matched records | Per-replicate quantification under `work/posttran_quantification/` |
| 8 | Step 7 counts + cluster reference | Element-count table under `work/posttran_element_mapping/` |
| 9 | Step 8 DNA/RNA replicate tables + negative controls | Activity-by-element table (user `--output-path`) |

Typical Step 5 retained artifacts (ExactID filenames; domains follow `--id-columns`):

- `work/id_map_generation/pretran_step5_id_crosswalk.tsv.gz`
- `work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz`
- `work/id_map_generation/pretran_step5_PID_cluster_reference.tsv.gz` (when PID is declared)

Typical Step 8 retained artifact per replicate:

- `work/posttran_element_mapping/<prefix>_step8_element_counts.tsv.gz`

For the exact eBC and pBC commands, summaries, validation checks, and
symptom-first recovery matrix, see [Steps 6–8](steps-6-8.md).
For the exact activity calculation and Step 9 completion contract, see
[Step 9: call activity](steps-9.md).

## PreTran profiles

| Profile | Grouped command | Typical `--id-columns` |
| --- | --- | --- |
| Dual orientation (CW + CCW), dual ID | `process_pretrans` | `EID,PID` |
| CW-only, EID-only | `process_pretrans_cw_only` | `EID` |

ID columns are **CLI-declared** (not discovered from headers). Declared names
must match the PreTran delimited header exactly.

## Forward/reverse reference pairing

For dual-orientation assays, the forward and reverse tested-library FASTA files
form a **one-to-one positional pair**:

- Both files must contain the same number of records (`N`).
- Record `i` in the forward file and record `i` in the reverse file represent the **same physical element** in opposite orientations.
- Header strings may differ (for example `1.fwd` vs `1.rev`); pairing is by **record order**, not by matching `Element` names.
- Headers must be unique within each file.

This pairing contract is used by `process_pretrans` (which supplies each
orientation’s FASTA to Step 3) and by orientation-scatter QC
(`plot_orientation_scatter`). ExogeneousSequences export uses repeatable
`--reference` paths in CLI order instead; it does not require equal record
counts. See [Artifact formats](formats.md) and [Export CLI](cli/export.md).

## Branch completion

A full dual-branch experiment produces **two** final activity tables:

| Branch | Typical cluster reference | Typical output |
| --- | --- | --- |
| eBC | `pretran_step5_EID_cluster_reference.tsv.gz` | `EID-ActivityByElement.tsv.gz` |
| pBC | `pretran_step5_PID_cluster_reference.tsv.gz` | `PID-ActivityByElement.tsv.gz` |

EID-only / eBC-only libraries run the eBC branch only (no PID cluster artifact,
no pBC `call_activity` / export).

Run `process_posttrans` once per replicate with the matching branch cluster
reference, then run `call_activity` once per branch present.

## Grouped commands

Most users run the grouped orchestration commands rather than individual steps:

| Command | Steps | Purpose |
| --- | --- | --- |
| `prep_lib` | 1 → 2 | Trim + delimited records (once per library) |
| `process_pretrans` | 3 → 4 → 5 | Dual-orientation PreTran + ID maps (once) |
| `process_pretrans_cw_only` | 3 → 4 → 5 | CW-only PreTran + ID maps (once) |
| `process_posttrans` | 6 → 7 → 8 | One post-transfection replicate |
| `call_activity` | 9 | Activity calling (once per branch) |

Grouped commands wire step-to-step intermediates automatically. By default they
delete orchestrator-managed intermediates after success while retaining final
outputs and `*_summary.json` files. Pass `--no-delete-intermediate` to keep
intermediates. Details and examples: [Pipeline CLI](cli/pipe.md).
