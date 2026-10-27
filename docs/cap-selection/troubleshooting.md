# Cap assay troubleshooting

Check each step's summary JSON before using its output in the next stage.
Steps 2 and 3 also write rejected-read FASTQs and a rejection table
(`read_name`, `captures`, `reason`, `evidence`); inspect them before changing
inputs.

| Symptom | What to check |
| --- | --- |
| `invalid command: step2-clip-construct-flank` | The command was removed in 0.2.0b5. Use `step2-identify-and-clip` with a version 1 `--layout`; see [Migrating to 0.2.0b5](migrating-to-0.2.0b5.md). |
| `unrecognized arguments: --star …`, `--star-index-dir`, `--max-multimaps`, `--random-seed`, or `--max-pair-mismatches` | STAR-era options are removed. Drop them; use `--max-pair-edits` for edit ceilings. |
| Step 3 `invalid choice: 'both'` or missing `--rna-strand` | Step 3 requires `plus` or `minus`. Give the same value to Step 4. |
| Step 1 fails | No pairs remained after preparation or UMI filtering, or the fastp UMI annotation is missing or malformed. |
| Step 2 fails with an invalid layout | Fix the layout JSON: `schema_version` must be the integer `1`, every segment needs boolean `retain`, retained segments must be contiguous, and at most one `"rest"` segment per mate. |
| Step 2 retains few or zero pairs | Read `rejection_reasons` in the summary. `anchor_or_length_mismatch` suggests anchors, positions, or lengths do not match the reads; `short_retained_mate` suggests reads are shorter than `--min-retained-length` after clipping; `disagreeing_repeated_capture` suggests a capture's `normalize` orientation is wrong. |
| Step 3 fails before reading pairs | The barcode map or FASTA is invalid: missing `barcode`/`Element` columns, a barcode assigned to two Elements, an Element absent from the FASTA, or a non-A/C/G/T/N sequence. `--bam-sort-memory` must give at least 1 MiB per thread. |
| Step 3 fails on a missing field or malformed annotation | The inputs are not Step 2 outputs (for example Step 1 FASTQs), or a `--barcode-field` name is not a capture in the layout. |
| Step 3 rejects many pairs as `unknown_barcode` or `disagreeing_lookup_identities` | The barcode map does not use the normalized capture values, the wrong fields are selected, or a capture's `normalize` orientation is wrong. |
| Step 3 rejects many pairs as `no_acceptable_placement` | The strand is wrong, the reference contains construct flanks or the retained reads include non-element sequence, or `--max-pair-edits` is too low. |
| Step 4 strand contradiction | The Step 4 `--rna-strand` value differs from the Step 3 value. |
| Step 4 zero eligible pairs | Read `rejection_counts` and `edit_histogram` in the summary. |

A partially processed Step 2 or Step 3 run (summary `complete: false` or
`diagnostics_status: "incomplete"`) is not a complete rejection audit. Rerun
into a fresh output directory after fixing the cause; commands refuse to
overwrite existing outputs.

The [cap CLI reference](../cli/cap-assay.md) defines each stage's failure
conditions and output summary fields. Release-specific scope limits are listed
under [Known limitations](known-limitations.md).
