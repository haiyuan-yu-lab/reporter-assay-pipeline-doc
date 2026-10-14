# Cap assay format contracts

This page describes the public artifact handoffs for the released **0.2.0b3** cap workflow. Cap constructs use a FASTA reference and a separate clipping configuration; they do not use the reporter assay's parsing-layout schema. CAP does not publish or require a reference-builder manifest.

## Layout and configuration schemas

Step 2 `--clip-layout` takes UTF-8 JSON with `schema_version: "1"`, a filename-safe `clip_id`, non-empty `layouts`, `clip_targets`, `unmatched_pairs: "keep"`, and `empty_read: "error"`. Each layout has an ID and ordered fixed–variable–fixed regions; fixed sequences use A/C/G/T and the variable region names a PID and its length. Targets independently select mate, end, layout IDs, and matching mode. R1 5′ targets use `complete_layout`; R2 3′ targets use `reverse_complement_overlap` with a positive minimum overlap. Omit targets for a mate that should not be clipped. Full validation and matching behavior is in the [Step 2 CLI contract](../cli/cap-assay.md#step2-clip-construct-flank-optional).

This clipping JSON is an optional processing configuration. It is distinct from reporter parsing schemas, and is not a construct reference or a Step 3 input.

## Inputs

| Stage | Input contract |
| --- | --- |
| External reference preparation | Tested-element FASTA plus one-record FASTA per fixed adapter; right adapter may be omitted. Concatenated records preserve element IDs. |
| Step 1 | Paired FASTQ or gzip FASTQ; R1 supplies the 12-base UMI, which is stored in the canonical `:UMI_<12 A/C/G/T>` read-name suffix. |
| Step 2 (optional) | Synchronized paired FASTQ outputs from Step 1 or another compatible source, plus the clip-layout JSON above. |
| Step 3 | Synchronized compatible paired FASTQs and an ordinary standalone construct-derived FASTA. Complete sequence must be unique across distinct FASTA IDs. No builder annotations, provenance, or manifest is required. |
| Step 4 | One coordinate-sorted BAM with a single read group matching the library prefix and the required UMI suffix on each read. A BAI and Step 3 provenance are not required. |

Reference assembly is an external, unnumbered prerequisite, not a CAP step or runtime dependency. See [Prepare inputs and reference](prepare-inputs.md) for the adapter FASTA recipe.

## Outputs and intermediate handoffs

| Producer | Handoff artifacts |
| --- | --- |
| Step 1 | `<prefix>_R1.trim.fq.gz`, `<prefix>_R2.trim.fq.gz`, and `<prefix>_step1_summary.json` (exact paths are reported in the summary). |
| Optional Step 2 | `<prefix>_R1.clip.fq.gz`, `<prefix>_R2.clip.fq.gz`, and `<prefix>_step2_summary.json`. |
| Step 3 | `<prefix>_step3_alignment.bam`, its `.bai`, and `<prefix>_step3_summary.json`; Step 4 consumes the BAM. |
| Step 4 | Policy-selected endpoint bigWigs and `<prefix>.step4_summary.json`. `both` emits `.5pl.bw`, `.5mn.bw`, `.3pl.bw`, `.3mn.bw`; `plus` or `minus` emits the two corresponding tracks. |

Step 4 outputs `.5pl/.5mn` are R2 5′ cap signal, while `.3pl/.3mn` are R1-derived RNA 3′ polymerase-position proxy. Plus/minus are relative to the construct-derived reference. Minus-track values are negative; their absolute values are observation counts. Step 4 summary JSON records pair totals, rejection counts, mismatch histogram, track metrics, tool/version details, and selected policy. These JSON summaries are diagnostics and completion records, not inputs to the next step.

## Step 4 endpoint bigWigs

Each retained eligible molecule contributes one R2 cap observation and one R1 proxy observation, both assigned using the R1 biological RNA strand (forward R1 is plus; reverse R1 is minus). Coordinates are sequenced 5′ endpoints. Track sequence dictionaries and coordinate extents come from the admitted BAM `@SQ` dictionary. The selected tracks share that dictionary; policy-omitted tracks are not created. BEDTools may combine adjacent equal-count positions into intervals internally, while the published bigWigs preserve the per-position counts.

See [Step 4 operations](step4.md) for policy selection and the [CLI reference](../cli/cap-assay.md#step4-post-alignment-processing) for admission, filters, and summary details.
