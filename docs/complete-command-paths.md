# Complete command paths

This page gives two complete, copyable command narratives for release
**0.1.0b3**. Both use the same de-identified experiment:

- PreTran libraries: `PreTran_CW` and `PreTran_CCW`;
- eBC branch: `eBC_DNA_rep1..3` and `eBC_RNA_rep1..3`;
- pBC branch: `pBC_DNA_rep1..3` and `pBC_RNA_rep1..3`;
- forward and reverse tested-element references;
- one layout schema per library family; and
- one negative-control list in the shared `Element` namespace.

`eBC` and `pBC` are assay branches. `EID` and `PID` are identifier domains:
the eBC branch uses EID and the pBC branch uses PID. `CW` is the clockwise
(forward) construct orientation and `CCW` is counter-clockwise (reverse).
Every FASTQ name includes both paired-read directions (`R1` and `R2`). The
names and paths below are placeholders; they do not identify a real sample or
institution.

For column, summary, tolerated-row, and fatal-condition contracts, follow the
canonical [input](input-preparation.md), [Steps 1–2](steps-1-2.md),
[Steps 3–5](steps-3-5.md), [Steps 6–8](steps-6-8.md), and
[Step 9](steps-9.md) pages. The [artifact format reference](formats.md) is the
canonical description of each handoff. The [workflow](workflow.md) defines
stage ownership and retained outputs, the [QC reference](cli/qc.md) and
[export reference](cli/export.md) define downstream consumers, and the
[known limitations](known-limitations.md) page records release-specific
failures and recovery links.

## Before either path

Prepare `<project_dir>`, `<raw_dir>`, `<schema_dir>`, `<reference_dir>`,
`<control_dir>`, and `<out_dir>` as local directories. Validate that all 14
raw paired FASTQs are readable, gzip-valid, non-empty, and synchronized; that
the forward and reverse FASTAs have equal record counts and positional pairs;
that the schemas match their libraries; and that
`<control_dir>/negative_controls.txt` lists at least one retained negative
control. See [input readiness](input-preparation.md) for the checks.

The examples use POSIX shell syntax and ordinary Linux tools. They are
Markdown examples, not downloadable scripts. Set the variables to paths that
exist in your environment:

```sh
project_dir="<project_dir>"
raw_dir="<raw_dir>"
schema_dir="<schema_dir>"
reference_dir="<reference_dir>"
control_dir="<control_dir>"
out_dir="<out_dir>"
mkdir -p "$project_dir" "$out_dir"
```

## Grouped path: normal operation

The grouped path runs each library's Step 1→2 preparation, shared PreTran
Steps 3→5, each post-transfection replicate's Steps 6→8, and one Step 9 call
per branch. It is resumable at command boundaries: do not rerun successful
commands unless their retained handoff is absent or invalid.

### 1. Prepare all 14 libraries

`prep_lib` produces `work/trimmed/<prefix>_R1.trim.fq.gz`,
`<prefix>_R2.trim.fq.gz`, fastp reports, and a Step 1 summary, then consumes
those exact paths to produce `work/delimited/<prefix>_step2_records.tsv.gz`
and a Step 2 summary.

```sh
for prefix in PreTran_CW PreTran_CCW; do
  yulab_reporter_pipe prep_lib \
    --library-prefix "$prefix" \
    --input-r1 "$raw_dir/${prefix}_R1.fastq.gz" \
    --input-r2 "$raw_dir/${prefix}_R2.fastq.gz" \
    --layout-schema "$schema_dir/pretran_layout.json" \
    --project-dir "$project_dir"
done

for branch in eBC pBC; do
  for material in DNA RNA; do
    for rep in 1 2 3; do
      prefix="${branch}_${material}_rep${rep}"
      yulab_reporter_pipe prep_lib \
        --library-prefix "$prefix" \
        --input-r1 "$raw_dir/${prefix}_R1.fastq.gz" \
        --input-r2 "$raw_dir/${prefix}_R2.fastq.gz" \
        --layout-schema "$schema_dir/${branch}_${material}_layout.json" \
        --project-dir "$project_dir"
    done
  done
done
```

Stop on any non-zero command or failed summary. A non-zero Step 2 mismatch
count is tolerated only when the summary is successful and retained records
are non-empty. The grouped command deletes its orchestrator-managed Step 1
intermediates after success by default; it retains the Step 2 records and all
summary/report deliverables. Use `--no-delete-intermediate` before rerunning a
diagnostic path. A deletion failure fails the grouped invocation; preserve the
successful summaries and inspect the directory before deciding what to remove.

### 2. Build the dual-orientation, dual-ID PreTran map

This command consumes the two Step 2 PreTran records, runs CW against the
forward reference and CCW against the reverse reference, then merges the
orientation-resolved records and emits the crosswalk plus EID and PID cluster
references.

```sh
yulab_reporter_pipe process_pretrans \
  --id-columns EID,PID \
  --cw-prefix PreTran_CW \
  --ccw-prefix PreTran_CCW \
  --cw-records "$project_dir/work/delimited/PreTran_CW_step2_records.tsv.gz" \
  --ccw-records "$project_dir/work/delimited/PreTran_CCW_step2_records.tsv.gz" \
  --forward-reference "$reference_dir/elements_forward.fa" \
  --reverse-reference "$reference_dir/elements_reverse.fa" \
  --project-dir "$project_dir"
```

Retained outputs are `pretran_step5_id_crosswalk.tsv.gz`,
`pretran_step5_EID_cluster_reference.tsv.gz`,
`pretran_step5_PID_cluster_reference.tsv.gz`, and stage summaries. Step 3
and Step 4 intermediates may be deleted after success; use
`--no-delete-intermediate` to retain them for debugging. If any nested stage
fails, the grouped command stops, retains the failed-run intermediates and
summaries, and returns non-zero. Read the first failed summary and resume with
the corresponding [individual commands](#individual-path-debugging-and-resumption).

### 3. Process all 12 post-transfection replicates

The eBC branch uses `EID` and the EID cluster reference; pBC uses `PID1` and
the PID cluster reference. Each invocation consumes its own Step 2 record and
passes the Step 6 matched records to Step 7, then Step 7 quantification to
Step 8. The retained handoff for every prefix is
`work/posttran_element_mapping/<prefix>_step8_element_counts.tsv.gz` plus its
summary.

```sh
for branch in eBC pBC; do
  case "$branch" in
    eBC) id_field=EID; input_id_col=EID; cluster="$project_dir/work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz" ;;
    pBC) id_field=PID1; input_id_col=PID1; cluster="$project_dir/work/id_map_generation/pretran_step5_PID_cluster_reference.tsv.gz" ;;
  esac
  for material in DNA RNA; do
    for rep in 1 2 3; do
      yulab_reporter_pipe process_posttrans \
        --library-prefix "${branch}_${material}_rep${rep}" \
        --id-field "$id_field" \
        --cluster-reference "$cluster" \
        --input-id-col "$input_id_col" \
        --input-count-col MoleculeCount \
        --project-dir "$project_dir"
    done
  done
done
```

`process_posttrans` deletes its Step 6 and Step 7 intermediates after a
successful invocation and retains Step 8 output and summaries. A failure for
one prefix stops that invocation and the loop; successful other prefixes are
not evidence that the failed replicate is complete. Rerun the failed prefix
with `--no-delete-intermediate` and the individual path after correcting the
reported input, reference, schema, or I/O problem.

### 4. Call activity for both branches

Step 9 consumes all three DNA and all three RNA Step 8 tables positionally,
uses the same negative-control list, and emits one branch-specific
`activity-by-element` table and summary.

```sh
for branch in eBC pBC; do
  case "$branch" in
    eBC) domain=EID ;;
    pBC) domain=PID ;;
  esac
  yulab_reporter_pipe call_activity \
    --dna-records \
      "$project_dir/work/posttran_element_mapping/${branch}_DNA_rep1_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_DNA_rep2_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_DNA_rep3_step8_element_counts.tsv.gz" \
    --rna-records \
      "$project_dir/work/posttran_element_mapping/${branch}_RNA_rep1_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_RNA_rep2_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_RNA_rep3_step8_element_counts.tsv.gz" \
    --negative-control-annotation "$control_dir/negative_controls.txt" \
    --output-path "$out_dir/${domain}-ActivityByElement.tsv.gz" \
    --project-dir "$project_dir"
done
```

Completion requires both tables to be non-empty, have the exact
`activity-by-element` header, and have successful summaries. Retain the two
tables, their summaries, and any selected QC/export outputs. A failed branch
does not make the other branch complete; repair and rerun only the failed
branch after checking the shared element intersection and retained controls.

## Individual path: debugging and resumption

Use this path when a grouped command stops or when each producer-to-consumer
handoff must be inspected. The commands use the same prefixes, files,
references, schemas, and controls as the grouped path. After each command,
require a successful summary and a non-empty expected artifact before running
the next command.

### Steps 1–2 for every library

Run the following loop once for the two PreTran libraries and once for all
12 branch libraries. Step 1's cleaned `R1.trim.fq.gz` and `R2.trim.fq.gz`
are the explicit Step 2 inputs; Step 2's records are the Step 3/6 inputs.

```sh
for prefix in PreTran_CW PreTran_CCW; do
  yulab_reporter_pipe step1 --library-prefix "$prefix" \
    --input-r1 "$raw_dir/${prefix}_R1.fastq.gz" --input-r2 "$raw_dir/${prefix}_R2.fastq.gz" \
    --project-dir "$project_dir"
  yulab_reporter_pipe step2 --library-prefix "$prefix" \
    --input-r1 "$project_dir/work/trimmed/${prefix}_R1.trim.fq.gz" \
    --input-r2 "$project_dir/work/trimmed/${prefix}_R2.trim.fq.gz" \
    --layout-schema "$schema_dir/pretran_layout.json" --project-dir "$project_dir"
done

for branch in eBC pBC; do
  for material in DNA RNA; do
    for rep in 1 2 3; do
      prefix="${branch}_${material}_rep${rep}"
      yulab_reporter_pipe step1 --library-prefix "$prefix" \
        --input-r1 "$raw_dir/${prefix}_R1.fastq.gz" --input-r2 "$raw_dir/${prefix}_R2.fastq.gz" \
        --project-dir "$project_dir"
      yulab_reporter_pipe step2 --library-prefix "$prefix" \
        --input-r1 "$project_dir/work/trimmed/${prefix}_R1.trim.fq.gz" \
        --input-r2 "$project_dir/work/trimmed/${prefix}_R2.trim.fq.gz" \
        --layout-schema "$schema_dir/${branch}_${material}_layout.json" --project-dir "$project_dir"
    done
  done
done
```

### Steps 3–5, then 6–8, then 9

Run Step 3 once for each orientation, handing its output explicitly to Step 4;
hand Step 4's merged counts explicitly to Step 5:

```sh
yulab_reporter_pipe step3 --library-prefix PreTran_CW \
  --input-records "$project_dir/work/delimited/PreTran_CW_step2_records.tsv.gz" \
  --reference "$reference_dir/elements_forward.fa" --id-columns EID,PID --project-dir "$project_dir"
yulab_reporter_pipe step3 --library-prefix PreTran_CCW \
  --input-records "$project_dir/work/delimited/PreTran_CCW_step2_records.tsv.gz" \
  --reference "$reference_dir/elements_reverse.fa" --id-columns EID,PID --project-dir "$project_dir"
yulab_reporter_pipe step4 \
  --records "$project_dir/work/pretran_orientation/PreTran_CW_step3_orientation_resolved.tsv.gz" \
  --records "$project_dir/work/pretran_orientation/PreTran_CCW_step3_orientation_resolved.tsv.gz" \
  --id-columns EID,PID --project-dir "$project_dir"
yulab_reporter_pipe step5 \
  --pretran-counts "$project_dir/work/pretran_merge_counts/pretran_step4_merged_counts.tsv.gz" \
  --id-columns EID,PID --project-dir "$project_dir"
```

For each of the 12 post-transfection prefixes, run Step 6 with the Step 2
records and branch reference, Step 7 with the Step 6 matched file, and Step 8
with the Step 7 quantification and the same cluster reference:

```sh
for branch in eBC pBC; do
  case "$branch" in
    eBC) id_field=EID; input_id_col=EID; cluster="$project_dir/work/id_map_generation/pretran_step5_EID_cluster_reference.tsv.gz" ;;
    pBC) id_field=PID1; input_id_col=PID1; cluster="$project_dir/work/id_map_generation/pretran_step5_PID_cluster_reference.tsv.gz" ;;
  esac
  for material in DNA RNA; do
    for rep in 1 2 3; do
      prefix="${branch}_${material}_rep${rep}"
      yulab_reporter_pipe step6 --library-prefix "$prefix" --id-field "$id_field" \
        --input-records "$project_dir/work/delimited/${prefix}_step2_records.tsv.gz" \
        --cluster-reference "$cluster" --project-dir "$project_dir"
      yulab_reporter_pipe step7 --library-prefix "$prefix" \
        --input-records "$project_dir/work/posttran_id_matching/${prefix}_step6_matched_records.tsv.gz" \
        --project-dir "$project_dir"
      yulab_reporter_pipe step8 --library-prefix "$prefix" \
        --input-records "$project_dir/work/posttran_quantification/${prefix}_step7_quantification.tsv.gz" \
        --element-reference "$cluster" --input-id-col "$input_id_col" \
        --input-count-col MoleculeCount --project-dir "$project_dir"
    done
  done
done
```

Finally run Step 9 once per branch with the three corresponding Step 8 DNA
and RNA paths. This is the final explicit producer-to-consumer handoff in the
individual path:

```sh
for branch in eBC pBC; do
  case "$branch" in
    eBC) domain=EID ;;
    pBC) domain=PID ;;
  esac
  yulab_reporter_pipe step9 \
    --dna-records \
      "$project_dir/work/posttran_element_mapping/${branch}_DNA_rep1_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_DNA_rep2_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_DNA_rep3_step8_element_counts.tsv.gz" \
    --rna-records \
      "$project_dir/work/posttran_element_mapping/${branch}_RNA_rep1_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_RNA_rep2_step8_element_counts.tsv.gz" \
      "$project_dir/work/posttran_element_mapping/${branch}_RNA_rep3_step8_element_counts.tsv.gz" \
    --negative-control-annotation "$control_dir/negative_controls.txt" \
    --output-path "$out_dir/${domain}-ActivityByElement.tsv.gz" \
    --project-dir "$project_dir"
done
```

Step 9's output and summary are the final handoff; downstream QC and export
consume only successful, schema-conforming activity tables.

### Failure, deletion, and resumption rules

Individual commands never delete a producer's input. A failed command leaves
its readable outputs and summary when possible; treat a failed summary or an
empty output as unusable and do not advance. For grouped commands, successful
completion removes only orchestrator-managed intermediates when deletion is
enabled; final deliverables and summaries remain. A deletion error makes that
grouped invocation fail and its run directory should be retained until the
error is resolved. `--no-delete-intermediate` is the safe setting for
diagnosis and makes every handoff inspectable. Resume from the first failed
stage, not from a later file that merely exists. See the stage-specific
[failure matrices](steps-1-2.md#symptom-first-recovery),
[PreTran recovery](steps-3-5.md#symptom-first-recovery),
[PostTran recovery](steps-6-8.md#validation-and-symptom-first-recovery), and
[activity recovery](steps-9.md#failures-and-recovery).

## CW-only / EID-only variation

This reduced profile is separate from the complete dual-branch example. Omit
`PreTran_CCW`, the reverse FASTA, and all PID columns/references. Prepare only
`PreTran_CW` and eBC DNA/RNA libraries, use `process_pretrans_cw_only
--id-columns EID`, process those six post-transfection replicates with the EID
cluster reference, and call Step 9 once to emit `EID-ActivityByElement`. Omit
the pBC Step 6–8 commands, PID cluster reference, PID activity call, and any
pBC QC/export. The CW-only grouped command and its rejected CCW flags are
documented in the [Pipeline CLI reference](cli/pipe.md#process_pretrans_cw_only-step3-cw-step4-step5).
