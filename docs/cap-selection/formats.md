# Cap assay format contracts

This page describes the public artifact handoffs for the released **0.2.0b5**
cap workflow. CAP uses its own layout JSON, barcode map, and element-only
FASTA; they are not the reporter assay's parsing-layout schema. CAP does not
publish or require a reference-builder manifest. Artifacts from releases
before 0.2.0b5 are not compatible; see [Migrating to
0.2.0b5](migrating-to-0.2.0b5.md).

## Inputs

| Stage | Input contract |
| --- | --- |
| Step 1 | Paired FASTQ or gzip FASTQ; R1 supplies the 12-base UMI, which is stored in the canonical `:UMI_<12 A/C/G/T>` read-name suffix of both mates. |
| Step 2 | Synchronized gzip paired FASTQs from Step 1 or another compatible source with agreeing UMI suffixes, plus the [layout JSON](#step-2-layout-json-schema-version-1). |
| Step 3 | Gzip paired FASTQs carrying a well-formed [CAP1 annotation](#cap1-read-name-annotation) and UMI suffix, an [element-only FASTA](#step-3-element-only-reference-fasta), and a [barcode map](#step-3-barcode-map-tsv). Step 2 provenance is not required. |
| Step 4 | One coordinate-sorted BAM with a single read group matching the library prefix and the required UMI suffix on each read. A BAI, Step 3 provenance, and CAP-specific tags are not required. |

## Step 2 layout JSON (schema version 1)

UTF-8 JSON object with integer `schema_version: 1` (not the string `"1"`) and
a non-empty `layouts` array. Each layout has a unique non-empty `name` and
non-empty ordered `r1` and `r2` segment arrays. Every segment sets boolean
`retain` and has one of these kinds:

| `kind` | Fields | Meaning |
| --- | --- | --- |
| `fixed` | `sequence` (A/C/G/T), optional `max_mismatches` (non-negative integer) | Complete positional anchor; substitutions allowed up to `max_mismatches`, else `--max-anchor-mismatches` (default 1) |
| `capture` | `name` (non-empty string), `length` (positive integer or `"rest"`), optional `normalize` (`forward` default, or `reverse_complement`), optional `alphabet` (unique uppercase subset of A/C/G/T/N, default `ACGT`) | Extract a named value |
| `sequence` | `length` (positive integer or `"rest"`) | Bases that are not captured |

Rules:

- At most one `"rest"` segment per mate; its length is the read length minus
  every other segment length, even when it is not the last segment. Segment
  lengths account for the complete read.
- Retained segments form one non-empty contiguous interval per mate, and each
  retained mate must have at least `--min-retained-length` bases (default 15).
  Capturing and retaining a segment are independent.
- Captures are validated against their alphabet before normalization.
  Normalization changes capture metadata only; retained sequence and qualities
  are sliced from the original read unchanged.
- Repeated captures with the same name, in either mate, must agree after
  normalization. Differently named captures are independent.
- A pair succeeds only when exactly one layout matches. Array order never
  selects a winner.
- Capture names are arbitrary; no name (including `PID`) has built-in
  meaning. Names acquire identity meaning only through Step 3
  `--barcode-field`.

Invalid schema, field types, lengths, alphabets, anchors, or retained
intervals fail before any read is processed. See [Migrating to
0.2.0b5](migrating-to-0.2.0b5.md#layout-json) for a worked example.

## CAP1 read-name annotation

Step 2 appends `|CAP1=<payload>` to the first name token of both mates,
immediately before the unchanged `:UMI_<12 A/C/G/T>` suffix. The payload is
unpadded URL-safe base64 of canonical UTF-8 JSON: a string-to-string object of
every capture name and normalized uppercase value, with sorted keys and no
insignificant whitespace. The logical read name, `/1`/`/2` designation, and
any text after the first token are preserved. Duplicate annotations,
malformed payloads, mate disagreement, and names longer than SAM's
254-character limit fail the invocation; names are never truncated or hashed.
Externally prepared reads using the same annotation are valid Step 3 inputs.

## Step 3 element-only reference FASTA

Ordinary FASTA containing tested-element sequences only, without identity
barcodes or construct flanks. First-token IDs are unique and non-empty;
sequences are non-empty A/C/G/T/N and are normalized to uppercase. Unused
records are allowed. Identical sequences under different IDs are allowed and
are distinguished only by their assigned barcodes. Reference `N` is not a
wildcard. No index, manifest, annotation, or sidecar is used. Coordinates in
the BAM and tracks are positions within these element records.

## Step 3 barcode map TSV

UTF-8 tab-separated table with a header of unique column names that includes
`barcode` and `Element`; other columns are ignored.

```text
barcode	Element
ACGCTA	Element_001
TTGCAA	Element_001
GGATCC	Element_002
```

Barcodes are non-empty uppercase A/C/G/T. Each `Element` must be a FASTA ID.
Several barcodes may identify one Element; duplicate identical rows coalesce;
a barcode assigned to two Elements fails. Every row, used or not, is
validated before reads are processed. Lookup is exact, without error
correction or nearest-barcode rescue. This table is not the XP barcode-adder
CSV format.

## Outputs and intermediate handoffs

| Producer | Handoff artifacts | Diagnostics |
| --- | --- | --- |
| Step 1 | `<prefix>_R1.trim.fq.gz`, `<prefix>_R2.trim.fq.gz`, `<prefix>_step1_summary.json` | — |
| Step 2 | `<prefix>_R1.ident.fq.gz`, `<prefix>_R2.ident.fq.gz`, `<prefix>_step2_summary.json` | `<prefix>_step2_rejected_R1.fq.gz`, `<prefix>_step2_rejected_R2.fq.gz`, `<prefix>_step2_rejections.tsv.gz` |
| Step 3 | `<prefix>_step3_alignment.bam`, its `.bai`, `<prefix>_step3_summary.json`; Step 4 consumes the BAM | `<prefix>_step3_rejected_R1.fq.gz`, `<prefix>_step3_rejected_R2.fq.gz`, `<prefix>_step3_rejections.tsv.gz` |
| Step 4 | Policy-selected endpoint bigWigs and `<prefix>.step4_summary.json`. `both` emits `.5pl.bw`, `.5mn.bw`, `.3pl.bw`, `.3mn.bw`; `plus` or `minus` emits the two corresponding tracks. | — |

### Rejection tables

Steps 2 and 3 write gzip TSVs with columns `read_name`, `captures`, `reason`,
and `evidence`, one row per rejected pair in input order. `captures` and
`evidence` are canonical JSON; unavailable observations are `{}`. Empty
rejection artifacts are valid when every pair passes. Step 2 rejected FASTQs
contain original input pairs; Step 3 rejected FASTQs contain annotated,
clipped input pairs.

| Step | `reason` values |
| --- | --- |
| 2 | `anchor_or_length_mismatch`, `invalid_capture`, `disagreeing_repeated_capture`, `short_retained_mate`, `multiple_successful_layouts` |
| 3 | `unknown_barcode`, `disagreeing_lookup_identities`, `no_acceptable_placement`, `invalid_paired_geometry`, `tied_best_distinct_placements` |

Step 3 evidence holds the selected barcodes and resolved Elements for lookup
failures, and candidate counts, best edit scores, and a bounded number of
representative placements (with a truncation indicator) for placement
failures.

## Step 2 outputs and summary

`<prefix>_step2_summary.json` has `schema_version` `2.0` and `step`
`step2-identify-and-clip`.

| Field | Meaning |
| --- | --- |
| `status`, `complete`, `failure_reason` | `success` or `failed`; whether every input pair was evaluated; failure message (present only on failure) |
| `library_prefix`, `layout`, `max_anchor_mismatches` | Library token, resolved layout path, default anchor ceiling |
| `input_read_pairs`, `retained_read_pairs`, `rejected_read_pairs` | Exact counts for evaluated pairs |
| `rejection_reasons` | Map from reason to count |
| `pair_count_reconciled` | `input_read_pairs == retained_read_pairs + rejected_read_pairs` |
| `outputs` | Paths of all six artifacts |
| `resources` | Requested threads, worker processes, chunk bounds, and observed worker PIDs |

## Step 3 BAM and summary

The BAM is coordinate-sorted with `@SQ` lines for every FASTA record in input
order and one `@RG` whose ID is the library prefix. It contains accepted pairs
only, as mapped primary mates with `NH:i:1`, `HI:i:1`, `NM` per mate equal to
its base-edit count, `AS` equal to its negative, MAPQ 255, reference-span
TLEN, `xc:Z` (canonical capture JSON), and `xe:Z` (resolved Element ID).
CIGARs use `=` (match) and `X` (substitution) with optional internal `I`/`D`.

`<prefix>_step3_summary.json` has `schema_version` `4.0` and `stage`
`step3-alignment`.

| Field | Meaning |
| --- | --- |
| `status`, `failure_reason` | `success` or `failed`; nullable failure message |
| `rna_strand`, `max_pair_edits` | Effective strand and edit ceiling |
| `counts` | `processed_pairs`, `accepted_pairs`, `rejected_pairs`, `reasons` (map), and `accepted_plus_rejected_reconciled` |
| `diagnostics_complete`, `diagnostics_status` | Whether rejection evidence covers every input pair (`complete` / `incomplete`) |
| `diagnostic_examples`, `diagnostic_examples_truncated` | Up to 20 representative rejections |
| `tools` | Resolved `samtools` path and version |
| `artifacts` | Published artifact paths |
| `resources` | Requested threads, batch size, worker threads, sort memory per thread, and sort temporary root |

Summaries from earlier schema versions (STAR mapping and multimapping counts,
`effective_mapping_counts`, strand-rejected pairs) are not comparable.

## Step 4 endpoint bigWigs

Each retained eligible molecule contributes one R2 cap observation and one R1
proxy observation. R1 forward is biological RNA plus; R1 reverse is minus. R2
supplies the sequenced 5′ cap coordinate on its linked R1 strand, and the R1
sequenced 5′ coordinate is the RNA 3′ polymerase-position proxy. The proxy is
not a second cap-signal measurement. For reverse-strand reads the 5′
coordinate is taken from the CIGAR reference span, so internal deletions shift
it and insertions do not.

| Filename | Summary track key | Endpoint | Biological RNA strand | Published when |
| --- | --- | --- | --- | --- |
| `S.5pl.bw` | `cap_plus` | R2 sequenced 5′ cap signal | Plus | `both`, `plus` |
| `S.5mn.bw` | `cap_minus` | R2 sequenced 5′ cap signal | Minus | `both`, `minus` |
| `S.3pl.bw` | `proxy_plus` | R1 sequenced 5′ RNA 3′ proxy | Plus | `both`, `plus` |
| `S.3mn.bw` | `proxy_minus` | R1 sequenced 5′ RNA 3′ proxy | Minus | `both`, `minus` |

Plus and minus are relative to the element-only reference record, not genomic
or plasmid physical orientation. Coordinates are positions within the tested
element; they do not include construct-flank offsets, so tracks from releases
before 0.2.0b5 are not directly comparable. BigWig sequence names and lengths
match the admitted BAM `@SQ` dictionary in its original order. Values are raw
counts at occupied one-base `[start,end)` intervals. Plus tracks store
positive integers; minus tracks store negative integers whose absolute values
are counts. Zero-valued intervals are omitted. Selected tracks under `both`
publish the complete dictionary even when a track has no observations,
provided the invocation has eligible pairs. Tracks omitted by `plus`/`minus`
are absent.

BEDTools can merge adjacent endpoint positions with equal counts during aggregation. Published bigWigs preserve the count at every base. A two-base interval with count three represents six observations, two occupied positions, and maximum absolute pileup three.

## Step 4 summary JSON and QC fields

The file is `S.step4_summary.json`, where `S` is `--library-prefix`; `schema_version` is `2.0` and `step` is `step4-post-alignment-processing`. Values use native JSON types. At failure time unavailable values are `null`, never fabricated zeroes. Pure usage errors do not write a summary; an existing summary is not overwritten.

| Field | Type / meaning |
| --- | --- |
| `library_prefix`, `package_version`, `schema_version`, `step` | Strings identifying library, installed distribution, schema, and command. |
| `status`, `warnings`, `failure_reason` | `status` is `success` or `failed`; warnings is an array; failure reason is `null` on success and a concise message on failure. |
| `rna_strand`, `contradictory_pairs` | Selected policy (`both`, `plus`, `minus`); nullable count of otherwise eligible opposite-strand pairs when auditing completed. |
| `input_bam`, `output_dir`, `summary` | Resolved input/output paths and this summary path. |
| `effective_arguments` | Object with `threads`, `max_pair_edits`, `umi_dedup_method`, and `rna_strand`. |
| `resources` | Additive object recording the requested CPU budget and effective worker/phase resource evidence; values are JSON-native. |
| `samtools`, `samtools_version`; `bedtools`, `bedtools_version`; `umi_tools`, `umi_tools_version` | Resolved executable paths and probed version strings when known. |
| `pybigwig_version` | String when known, otherwise `null`. |
| `bam_sequences` | Ordered array of `{name, length}` entries from the BAM `@SQ` dictionary. |
| `read_group_id` | Sole admitted read-group ID; equals the library prefix. |
| `umi_dedup_method` | Selected UMI-tools method. |
| `pair_total_groups`, `eligible_pairs`, `rejected_pairs` | Integer distinct QNAME groups and pair counts; `eligible_pairs` is the retained count after deduplication. |
| `pre_dedup_eligible_pairs`, `umi_duplicate_pairs_removed` | Integer counts before and removed by UMI deduplication; `pre_dedup_eligible_pairs = eligible_pairs + umi_duplicate_pairs_removed`. |
| `rejection_counts` | Integer map for `excluded_flags`, `mapping_completeness`, `uniqueness`, `cigar`, `edit_ceiling`, and `geometry`. |
| `edit_histogram` | Map from string combined `NM(R1)+NM(R2)` base-edit totals to integer pair counts; only pairs whose primaries both carry valid `NM` contribute. |
| `tracks` | Object retaining all four canonical track keys. Published entries are resolved path strings; policy-omitted entries are `null`. |
| `track_observations` | Integer observation totals per canonical track key. Selected cap and proxy totals each reconcile to `eligible_pairs`; omitted tracks are zero. |
| `track_occupied_positions` | Integer distinct signaled positions per track; omitted tracks are zero. |
| `maximum_absolute_pileup` | Integer maximum per-position count per track; omitted tracks are zero. |
| `artifact_hashes` | SHA-256 strings per published bigWig track key; omitted tracks are `null`. |

The schema 1.0 fields `max_pair_mismatches`, `mismatch_ceiling`, and
`mismatch_histogram` are replaced, not aliased. For `both`,
`cap_plus + cap_minus` and `proxy_plus + proxy_minus` observations each equal
`eligible_pairs`. For `plus` the `cap_plus` and `proxy_plus` counts each equal
it; for `minus`, use the `minus` track keys. Zero eligible pairs before
deduplication or zero retained pairs after deduplication is failure.

See [Step 4 operations](step4.md) for running and checking the summary and the [cap CLI reference](../cli/cap-assay.md#step4-post-alignment-processing) for BAM admission and filtering rules.
