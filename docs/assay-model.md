# Assay model

This page documents the released **0.1.0b2** assay model and vocabulary.

This page explains the general dual reporter-assay model used by the
Reporter Assay Pipeline. It is the conceptual starting point for the
[workflow](workflow.md) and [canonical glossary](glossary.md).

## What the assay measures

The assay measures regulatory activity of a **tested element**: a DNA
sequence placed in a reporter construct. Sequencing measures the abundance of
reporter molecules before and after transfection. For each retained element,
the pipeline compares RNA abundance with DNA abundance and emits an
element-level activity score and call. The pipeline contract defines the
calculation; an `Active` or `Inactive` call is not a claim about a biological
mechanism beyond that calculation.

The public [QUASARR-seq publication](https://www.nature.com/articles/s41467-026-68780-y)
provides scientific context for this kind of quantitative reporter assay. Its
public [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE310760)
is provenance context only. The examples and contracts on this site are
generic and do not reproduce or require data from that study.

## Two assay branches and two identifier domains

A dual reporter assay has two measurement branches:

| Assay branch | Measurement | Identifier domain | Final table |
| --- | --- | --- | --- |
| **eBC** (enhancer barcode branch) | Enhancer activity | **EID** (enhancer identifier) | `EID-ActivityByElement` |
| **pBC** (promoter barcode branch) | Promoter activity | **PID** (promoter identifier) | `PID-ActivityByElement` |

An eBC or pBC label identifies an **assay branch**. EID or PID identifies an
**identifier domain** and the barcode values in that domain. These are related
but distinct concepts: an eBC input is not an “EID branch” by terminology,
and a PID is not a branch. The branch determines which post-transfection
barcode layout and cluster reference are used; the identifier domain
determines which identifier is resolved and counted.

The branches share the tested-element and orientation model, but each branch
has its own identifier observations, maps, replicate counts, and final
activity table. A CW-only/EID-only experiment uses the eBC branch and omits
the pBC branch; see [Workflow](workflow.md#pretran-profiles) for the
operational variation.

## Libraries and evidence

The pipeline uses three library roles:

1. **PreTran libraries** are sequenced before transfection. Their identifier
   and element observations establish which EID/PID values are associated with
   which tested elements. Dual-orientation PreTran inputs are represented as
   CW/forward and CCW/reverse libraries; they provide evidence for building
   the identifier map, not DNA/RNA activity replicates.
2. **PostTran DNA libraries** measure the DNA-side abundance of identifiers
   after transfection for an eBC or pBC branch. They provide the denominator
   for the corresponding activity ratio.
3. **PostTran RNA libraries** measure the RNA-side abundance of identifiers
   after transfection for an eBC or pBC branch. They provide the numerator for
   the corresponding activity ratio.

DNA and RNA are separate replicate sets. A Step 9 invocation aligns DNA and
RNA by replicate index and retains only elements present in every input
replicate. Negative-control elements in that retained analysis space establish
the normalization baseline. See [activity-by-element](formats.md#activity-by-element)
for the emitted table and the Step 9 CLI reference for exact options.

## Orientation and positional reference pairing

**CW** means clockwise, or forward, orientation of the tested element in the
construct. **CCW** means counter-clockwise, or reverse, orientation. In a
dual-orientation reference, the CW/forward and CCW/reverse FASTA records are
paired by **position**: record 1 in one file is paired with record 1 in the
other, record 2 with record 2, and so on.

The two orientations of one physical tested element can have different
`Element` identifiers. Therefore, Element names are not the pairing key and
must not be matched lexically to find the opposite orientation. Reference
record order is the positional key. Each reference file must have unique
headers within that file and the paired files must contain the same number of
records. The resulting opposite-orientation identifiers remain distinct
records for mapping, activity, and output; the positional pair is used when a
consumer needs to compare orientations, such as orientation-scatter QC.

## From molecules to an activity call

The conceptual lineage is:

```text
tested element
  -> PreTran identifier-to-element associations
  -> observed identifier / canonical identifier cluster references
  -> PostTran DNA and RNA molecule counts
  -> element-level replicate counts
  -> activity score, negative-control normalization, and ActivityCall
```

A **UMI** (unique molecular identifier) is deduplicated to count distinct
molecules rather than raw sequencing observations. PreTran UMI evidence is
merged into identifier-to-element counts. PostTran UMI evidence is resolved
through the appropriate branch's cluster reference, quantified per replicate,
and mapped back to elements before activity calling.

The exact formulas, pseudocount behavior, shared-element intersection, and
undefined-normalization failures belong to the Step 9 contract and are
documented with the activity command. This page supplies the model and
vocabulary needed to read those contracts.
