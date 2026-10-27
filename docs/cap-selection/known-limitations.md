# Cap assay known limitations

These limits describe the released **0.2.0b5** cap-selection workflow.

- The installed interface provides individual steps; there is no grouped command that runs the entire workflow or manages intermediate cleanup.
- Outputs, summaries, and tracks from releases before 0.2.0b5 are not compatible with this workflow. Regenerate Step 2–4 outputs in a fresh run directory; see [Migrating to 0.2.0b5](migrating-to-0.2.0b5.md).
- CAP does not create references, infer element boundaries from sequence, or restore information removed by clipping. Operators supply an element-only FASTA, a barcode→Element map, and a layout that describes their reads.
- Barcode identity lookup is exact. There is no barcode error correction, nearest-barcode rescue, or reference-wide search for pairs whose barcode is missing or unknown. No capture name, including `PID`, has an automatic lookup role.
- CAP does not infer barcode assignments. Libraries without a trustworthy barcode→Element map cannot be processed by the native workflow.
- Layout anchors are positional: they tolerate configured substitutions only, never indels, partial matches, or relocation.
- Step 3 searches one declared RNA strand per invocation (`plus` or `minus`) and has no `both` mode. Pairs from the other strand are not placed and are rejected.
- Step 3 aligns full clipped reads end to end within one Element. Spliced alignment, soft clipping, terminal insertions or deletions, and affine-gap scoring are not supported. Reads that extend beyond the element, for example into construct flanks, do not place.
- Two or more distinct best placements of a pair are rejected as ambiguous rather than resolved arbitrarily.
- The BAM carries no strand-policy marker: callers must repeat the same `--rna-strand` value at Steps 3 and 4. A restrictive mismatch fails Step 4 with its contradictory-pair count; a permissive mismatch (single-strand BAM passed as `both`) can only add empty tracks.
- Step 3 memory is not bounded by a constant: the element FASTA and barcode map are held in memory, and per-pair search covers all in-ceiling placements on the selected Element.
- Step 4 requires canonical fastp-produced 12-base A/C/G/T UMI suffixes and always performs paired UMI-tools deduplication. It has no bypass for missing UMI evidence or disabled deduplication, and does not add barcode or capture fields to molecule grouping.
- Step 4's R1 endpoint is a polymerase-position proxy for nascent RNA 3′ position; it is not a second cap-signal measurement. The R2 5′ endpoint supplies cap signal.
- Proxy coordinates retain their released convention; coordinate repair is deferred. The R1-derived signal is pause-biased and is not a validated exact RNA 3′ coordinate or an unbiased measure of polymerase occupancy.
- Track coordinates are positions within the tested element. CAP does not convert them to genomic or construct coordinates.
- Step 4 does not merge biological or technical replicates across libraries, normalize tracks between samples or to external references, infer transcript models, pause sites, or transcription start sites, or use R2 3′ sequencing endpoints.
- Step 4 deduplicates eligible pairs by extracted UMI, but does not perform barcode error correction or use UMIs to rescue pairs rejected by earlier filters.
- Zero retained Step 2 pairs, zero accepted Step 3 pairs, or zero eligible or retained Step 4 pairs is a failed run.

## Tool and validation boundaries

- Cap Step 1 uses the compatible `fastp` executable selected or found on `PATH`; its version is not pinned. Record the external tool version with each run because cleaning behavior may differ across versions.
- Native CAP acceptance for **0.2.0b5** is one fresh synthetic end-to-end run that executed real Steps 1–4 on the plus and minus strands at one and two threads, without STAR. No fresh real-library CAP assay PASS is claimed for 0.2.0b5, and no performance threshold is asserted.
- Release **0.2.0b3** included fresh four-library CAP acceptance and independent endpoint verification for the earlier STAR-based workflow. That evidence does not apply to, or certify, the native 0.2.0b5 workflow.

For failure recovery and summary checks, see [Cap assay troubleshooting](troubleshooting.md). Detailed supported inputs and outputs are in [Cap assay format contracts](formats.md).
