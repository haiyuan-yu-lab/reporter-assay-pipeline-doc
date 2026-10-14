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

## Step 4 endpoint bigWigs

Each retained eligible molecule contributes one R2 cap observation and one R1 proxy observation. R1 forward is biological RNA plus; R1 reverse is minus. R2 supplies the sequenced 5′ cap coordinate on its linked R1 strand, and the R1 sequenced 5′ coordinate is the RNA 3′ polymerase-position proxy. The proxy is not a second cap-signal measurement.

| Filename | Summary track key | Endpoint | Biological RNA strand | Published when |
| --- | --- | --- | --- | --- |
| `S.5pl.bw` | `cap_plus` | R2 sequenced 5′ cap signal | Plus | `both`, `plus` |
| `S.5mn.bw` | `cap_minus` | R2 sequenced 5′ cap signal | Minus | `both`, `minus` |
| `S.3pl.bw` | `proxy_plus` | R1 sequenced 5′ RNA 3′ proxy | Plus | `both`, `plus` |
| `S.3mn.bw` | `proxy_minus` | R1 sequenced 5′ RNA 3′ proxy | Minus | `both`, `minus` |

Plus and minus are relative to the construct-derived reference, not genomic or plasmid physical orientation. BigWig sequence names and lengths match the admitted BAM `@SQ` dictionary in its original order. Values are raw counts at occupied one-base `[start,end)` intervals. Plus tracks store positive integers; minus tracks store negative integers whose absolute values are counts. Zero-valued intervals are omitted. Selected tracks under `both` publish the complete dictionary even when a track has no observations, provided the invocation has eligible pairs. Tracks omitted by `plus`/`minus` are absent.

BEDTools can merge adjacent endpoint positions with equal counts during aggregation. Published bigWigs preserve the count at every base. A two-base interval with count three represents six observations, two occupied positions, and maximum absolute pileup three.

## Step 4 summary JSON and QC fields

The file is `S.step4_summary.json`, where `S` is `--library-prefix`; `schema_version` is `1.0` and `step` is `step4-post-alignment-processing`. Values use native JSON types. At failure time unavailable values are `null`, never fabricated zeroes. Pure usage errors do not write a summary; an existing summary is not overwritten.

| Field | Type / meaning |
| --- | --- |
| `library_prefix`, `package_version`, `schema_version`, `step` | Strings identifying library, installed distribution, schema, and command. |
| `status`, `warnings`, `failure_reason` | `status` is `success` or `failed`; warnings is an array; failure reason is `null` on success and a concise message on failure. |
| `rna_strand`, `contradictory_pairs` | Selected policy (`both`, `plus`, `minus`); nullable count of otherwise eligible opposite-strand pairs when auditing completed. |
| `input_bam`, `output_dir`, `summary` | Resolved input/output paths and this summary path. |
| `effective_arguments` | Object including `threads`, `max_pair_mismatches`, `umi_dedup_method`, and `rna_strand`. |
| `resources` | Additive object recording the requested CPU budget and effective worker/phase resource evidence; values are JSON-native. |
| `samtools`, `samtools_version`; `bedtools`, `bedtools_version`; `umi_tools`, `umi_tools_version` | Resolved executable paths and probed version strings when known. |
| `pybigwig_version` | String when known, otherwise `null`. |
| `bam_sequences` | Ordered array of `{name, length}` entries from the BAM `@SQ` dictionary. |
| `read_group_id` | Sole admitted read-group ID; equals the library prefix. |
| `umi_dedup_method` | Selected UMI-tools method. |
| `pair_total_groups`, `eligible_pairs`, `rejected_pairs` | Integer distinct QNAME groups and pair counts; `eligible_pairs` is the retained count after deduplication. |
| `pre_dedup_eligible_pairs`, `umi_duplicate_pairs_removed` | Integer counts before and removed by UMI deduplication; `pre_dedup_eligible_pairs = eligible_pairs + umi_duplicate_pairs_removed`. |
| `rejection_counts` | Integer map for `excluded_flags`, `mapping_completeness`, `uniqueness`, `cigar`, `mismatch_ceiling`, and `geometry`. |
| `mismatch_histogram` | Map from string combined `NM(R1)+NM(R2)` values to integer pair counts. |
| `tracks` | Object retaining all four canonical track keys. Published entries are resolved path strings; policy-omitted entries are `null`. |
| `track_observations` | Integer observation totals per canonical track key. Selected cap and proxy totals each reconcile to `eligible_pairs`; omitted tracks are zero. |
| `track_occupied_positions` | Integer distinct signaled positions per track; omitted tracks are zero. |
| `maximum_absolute_pileup` | Integer maximum per-position count per track; omitted tracks are zero. |
| `artifact_hashes` | SHA-256 strings per published bigWig track key; omitted tracks are `null`. |

For `both`, `cap_plus + cap_minus` and `proxy_plus + proxy_minus` observations each equal `eligible_pairs`. For `plus` the `cap_plus` and `proxy_plus` counts each equal it; for `minus`, use the `minus` track keys. Zero eligible pairs before deduplication or zero retained pairs after deduplication is failure.

See [Step 4 operations](step4.md) for running and checking the summary and the [cap CLI reference](../cli/cap-assay.md#step4-post-alignment-processing) for BAM admission and filtering rules.
