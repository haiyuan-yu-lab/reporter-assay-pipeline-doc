# Generate cap assay endpoint tracks (Step 4)

Step 4 consumes one compatible coordinate-sorted BAM and publishes strand-selected cap-signal and polymerase-position proxy tracks. Confirm Step 3 completed successfully, then pass its BAM and the same `--rna-strand` value used for alignment (`plus` or `minus`). Step 4 also accepts an externally produced BAM when it meets its admission contract; BAI, Step 3 provenance, and the `xc:Z`/`xe:Z` tags are not required.

Before running, confirm the BAM has one read group whose ID matches `--library-prefix`, is coordinate sorted, and has the required canonical `:UMI_<12 A/C/G/T>` suffix on every read name. Step 4 requires this UMI evidence and runs paired UMI-aware deduplication. Install samtools 1.12+, BEDTools 2.30+, and UMI-tools; pyBigWig is a Python dependency. The [CLI reference](../cli/cap-assay.md#step4-post-alignment-processing) lists all flags and admission details, and [resource guidance](resource-guidance.md) describes CPU and temporary-storage planning.

```bash
cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix LIB01 \
  --input-bam aligned/LIB01_step3_alignment.bam \
  --rna-strand plus \
  --output-dir tracks/
```

With `--rna-strand plus`, Step 4 publishes `.5pl.bw` (R2 5′ cap signal) and `.3pl.bw` (R1-derived RNA 3′ polymerase-position proxy); `minus` publishes `.5mn.bw` and `.3mn.bw`. The default `both` publishes all four tracks; for a single-strand Step 3 BAM the opposite-strand tracks are empty. The [format contract](formats.md#step-4-endpoint-bigwigs) defines track coordinates, signs, sequence dictionaries, filenames, and summary fields.

Pairs are eligible when both mates are uniquely placed primaries with full-query CIGARs (internal insertions and deletions allowed, no clipping or terminal gaps) and the combined base edits `NM(R1) + NM(R2)` do not exceed `--max-pair-edits` (default 4). The former `--max-pair-mismatches` option is removed. Reverse-read 5′ positions follow the CIGAR reference span, so deletions shift them and insertions do not.

Check `tracks/LIB01.step4_summary.json` (schema `2.0`) before using the tracks. Success has `status: "success"`; `eligible_pairs` is the retained molecule count after deduplication, and `pre_dedup_eligible_pairs = eligible_pairs + umi_duplicate_pairs_removed`. The selected cap-track observation total and proxy-track total each reconcile to `eligible_pairs`. The selected policy appears in `rna_strand`, combined edit counts in `edit_histogram`, and per-track observations, occupied positions, and maximum absolute pileup alongside them. The summary always contains all four track keys; tracks omitted by a restrictive policy have null paths/hashes and zero metrics. The [QC fields](formats.md#step-4-summary-json-and-qc-fields) are defined with the artifact contract; there is no separate cap QC executable.

If the summary reports failure, read `failure_reason` and `rejection_counts` before retrying. A strand contradiction means the Step 3 and Step 4 strand values differ; use the same value at both steps. A zero-eligible or zero-retained-pair run is a failure and produces no successful tracks. Check tool versions, BAM read-group/UMI requirements, and free space in the output/temp filesystem. See [cap troubleshooting](troubleshooting.md), [known limitations](known-limitations.md), and the [CLI reference](../cli/cap-assay.md#step4-post-alignment-processing) for recovery conditions and exact failure rules.
