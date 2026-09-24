# Known limitations in 0.2.0b1

These are limitations of the released build, not instructions to work around
them by guessing at undocumented behavior.

## `fastp` is not version-pinned

Step 1 and `prep_lib` invoke whichever compatible `fastp` executable is selected
or available on `PATH`. Record the external tool version with each run; this
release does not promise equivalent cleaning behavior across `fastp` versions.

## Release validation is unit-test-focused

The code repository has no continuous-integration workflow. Release
validation used the unit suite plus R-backed Step 9, QC, and ES contract
tests (`Rscript` 4.0.5, edgeR 3.32.1, limma 3.46.0, statmod 1.5.2). Large
local sandbox outputs are not a versioned release fixture.

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
