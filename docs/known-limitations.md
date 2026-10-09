# Known limitations in 0.2.0b3

These are limitations of the released build, not instructions to work around
them by guessing at undocumented behavior.

## Cap-selection strand correction and proxy coordinates

Release **0.2.0b3** corrects the R2-derived strand interpretation in **0.2.0b2**.
R1 forward means plus and R1 reverse means minus. R2 supplies the sequenced 5′
cap coordinate on that linked R1 strand. Selected-strand placement retention
and Step 4 cap/proxy assignment change; Step 3 `both` placement selection stays
the same. Reprocess earlier outputs when comparing corrected strand tracks.

Proxy coordinates retain their existing convention. Coordinate repair remains
deferred; the R1-derived signal is a pause-biased proxy, not a validated exact
RNA 3′ coordinate or unbiased polymerase occupancy measurement.

## `fastp` is not version-pinned

Step 1 and `prep_lib` invoke whichever compatible `fastp` executable is selected
or available on `PATH`. Record the external tool version with each run; this
release does not promise equivalent cleaning behavior across `fastp` versions.

## Release validation boundaries

The release candidate passed the implementation contract suite and both assay
harness suites. Fresh four-library CAP acceptance and independent endpoint
verification cover the corrected CAP behavior. Reporter resource-execution
changes have an explicit full-run waiver; the PreTran refactor requires no new
assay run. No fresh Reporter end-to-end PASS is claimed for **0.2.0b3**.
Outstanding Reporter integration and performance acceptance remains open.

The code repository has no hosted CI workflow. Step 9, QC and export contract
checks use the available R backend; see release notes for exact validation.

## Step 9 R backend and two-pair blocking

Step 9 requires `Rscript` with edgeR and limma. Three-or-more-pair fits also
require `statmod`. Two-pair fits use ordinary voom with **fixed replicate
blocks**; they do not estimate `duplicateCorrelation`.

## Resolved in 0.1.0b3

Release **0.1.0b3** routes every `yulab_reporter_pipe stepN --help` request to
the step-owned parser, resolving [public issue
5](https://github.com/DignoMor/reporter-assay-pipeline/issues/5). It also removes
the ineffective Step 6 `--min-match-length` option; matching remains exact
`ObservedID` to `CanonicalID` lookup, resolving [public issue
6](https://github.com/DignoMor/reporter-assay-pipeline/issues/6).

## Cap-selection Step 4

`cap-assay-pipeline step4-post-alignment-processing` intentionally does **not**:

- merge biological or technical replicates across libraries;
- normalize tracks between samples or to external references;
- infer transcript models, pause sites, or TSS calls from the bigWigs;
- consume R2 3′ sequencing endpoints;
- provide unbiased RNA polymerase II occupancy (the R1-derived tracks are a
  pause-biased polymerase-position proxy only).

Step 4 deduplicates eligible pairs by their extracted UMIs with UMI-tools,
but does **not** perform barcode error correction or UMI-based rescue of pairs
rejected by earlier filters. There is no grouped
whole-pipeline orchestration command; run Steps 1–4 explicitly.

## Cap-selection RNA strand policy

- Libraries pooling both construct orientations (CW/CCW) **and** both
  biological RNA strands cannot be resolved by `--rna-strand`; pool at most
  one axis (see [RNA strand policy](cap-selection/workflow.md#rna-strand-policy)).
- The BAM carries no strand-policy marker: callers must repeat the same
  `--rna-strand` value at Steps 3 and 4. A restrictive mismatch fails Step 4
  with its contradictory-pair count; a permissive mismatch (selected-strand
  BAM passed as `both`) can only add empty tracks.
- The policy never invents alignments: it selects among STAR's tied-best
  placements and cannot rescue a pair whose best placement is on the excluded
  strand (retained as unmapped, not remapped).
