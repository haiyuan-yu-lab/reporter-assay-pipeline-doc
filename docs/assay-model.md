# Assay overview

This package supports two assays that share construct context but answer
different questions and produce different outputs.

| Assay | What it measures | Main output | Start here |
| --- | --- | --- | --- |
| Reporter assay (QUASARR-seq) | Regulatory activity from RNA and DNA abundance after transfection | Element-level activity tables | [Reporter assay concepts](reporter-assay-concepts.md) |
| Cap assay (QUASARR-cap) | Nascent RNA endpoints after cap selection | Strand-selected endpoint bigWig tracks | [Cap assay concepts](cap-assay-concepts.md) |

The reporter pipeline maps barcode observations to tested elements and
compares post-transfection RNA and DNA counts. The cap pipeline uses identity
barcodes in each read pair to select a tested element, then aligns the pair to
that element to locate cap-selected RNA endpoints in element coordinates. These workflows have separate commands, input contracts, and
artifacts; a step number or file from one assay does not imply the same meaning
in the other.

Choose the assay-specific [reporter workflow](workflow.md) or [cap workflow](cap-selection/workflow.md)
to run an analysis. See [Quickstart](quickstart.md) to install and verify the
released package first.
