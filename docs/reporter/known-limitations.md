# Reporter known limitations in 0.2.0b4

These notes describe released reporter behavior and its validation boundary.

## `fastp` is not version-pinned

Step 1 and `prep_lib` invoke whichever compatible `fastp` executable is
selected or available on `PATH`. Record the external tool version with each
run; this release does not promise equivalent cleaning behavior across
`fastp` versions.

## Release validation boundaries

The release candidate passed the implementation contract suite and assay
harness suites. Reporter resource-execution changes have an explicit full-run
waiver; the PreTran refactor requires no new assay run. No fresh Reporter
end-to-end PASS is claimed for **0.2.0b4**. Outstanding Reporter integration
and performance acceptance remains open.

The code repository has no hosted CI workflow. Step 9, QC, and export contract
checks use the available R backend; see release notes for exact validation.

## Step 9 R backend and two-pair blocking

Step 9 requires `Rscript` with edgeR and limma. Three-or-more-pair fits also
require `statmod`. Two-pair fits use ordinary voom with **fixed replicate
blocks**; they do not estimate `duplicateCorrelation`. See [Step 9
requirements](../steps-9.md#r-dependencies).
