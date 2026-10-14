# Cap assay known limitations

These limits describe the released **0.2.0b3** cap-selection workflow.

- The installed interface provides individual steps; there is no grouped command that runs the entire workflow or manages intermediate cleanup.
- Reference assembly is external and unnumbered. CAP consumes a standalone FASTA and does not create references from construct-layout JSON or require assembly manifests.
- Step 2 clipping is optional and configuration-driven. It handles the defined R1 5′ complete-layout and R2 3′ reverse-complement-overlap targets; it is not a general adapter or indel-aware aligner.
- Step 3 requires distinct complete reference sequences across element IDs. Identical complete sequences are rejected rather than resolved to one identifier.
- `--rna-strand` is reference-relative, and Step 3 and Step 4 must use the same policy. Pooling both construct orientations with both RNA strands is unsupported because strand selection cannot disambiguate that combination.
- The BAM carries no strand-policy marker: callers must repeat the same `--rna-strand` value at Steps 3 and 4. A restrictive mismatch fails Step 4 with its contradictory-pair count; a permissive mismatch (selected-strand BAM passed as `both`) can only add empty tracks.
- The policy never invents alignments: it selects among STAR's tied-best placements and cannot rescue a pair whose best placement is on the excluded strand (retained as unmapped, not remapped).
- Step 4 requires canonical fastp-produced 12-base A/C/G/T UMI suffixes and always performs paired UMI-aware deduplication. It has no bypass for missing UMI evidence or disabled deduplication.
- Step 4's R1 endpoint is a polymerase-position proxy for nascent RNA 3′ position; it is not a second cap-signal measurement. The R2 5′ endpoint supplies cap signal.
- Proxy coordinates retain their released convention; coordinate repair is deferred. The R1-derived signal is pause-biased and is not a validated exact RNA 3′ coordinate or an unbiased measure of polymerase occupancy.
- Step 4 does not merge biological or technical replicates across libraries, normalize tracks between samples or to external references, infer transcript models, pause sites, or transcription start sites, or use R2 3′ sequencing endpoints.
- Step 4 deduplicates eligible pairs by extracted UMI, but does not perform barcode error correction or use UMIs to rescue pairs rejected by earlier filters.
- Zero eligible pairs before deduplication, or zero retained molecules after deduplication, is a failed Step 4 run.

## Tool and validation boundaries

- Cap Step 1 uses the compatible `fastp` executable selected or found on `PATH`; its version is not pinned. Record the external tool version with each run because cleaning behavior may differ across versions.
- Release **0.2.0b3** included fresh four-library CAP acceptance and independent endpoint verification. This is existing release evidence, not a new assay run or PASS for this documentation update.

For failure recovery and summary checks, see [Cap assay troubleshooting](troubleshooting.md). Detailed supported inputs and outputs are in [Cap assay format contracts](formats.md).
