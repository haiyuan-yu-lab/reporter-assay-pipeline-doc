# Reporter Assay Pipeline

This site documents release **0.2.0b5** of the Reporter Assay Pipeline. Choose
the assay that matches your data: the reporter assay measures element-level
activity from RNA and DNA counts; the cap assay produces strand-selected
nascent RNA endpoint tracks.

Release **0.2.0b5** replaces the cap assay's STAR-based alignment with
mandatory named-field identification and barcode-directed native alignment to
element-only references. This is a breaking change for cap assay runs: read
[Migrating to 0.2.0b5](cap-selection/migrating-to-0.2.0b5.md) before
upgrading. Reporter assay behavior is unchanged from **0.2.0b4**; only its
release identifiers advance.

## Choose an assay

- **Reporter assay:** start with the [reporter workflow](workflow.md) to prepare
  paired-end libraries and run the nine-step activity analysis. See
  [reporter assay concepts](reporter-assay-concepts.md) for PreTran, PostTran,
  branches, and identifiers.
- **Cap assay:** start with the [cap workflow](cap-selection/workflow.md) to
  prepare, identify, and align reads and generate endpoint tracks. See
  [cap assay concepts](cap-assay-concepts.md) for barcode-directed identity,
  element coordinates, reference-relative RNA strand, and the two endpoint
  measurements.

## Find guidance by task

- First installation: [Quickstart](quickstart.md).
- Understand how the assays relate: [Assay overview](assay-model.md).
- Understand reporter normalization: [Reporter assay normalization](reporter-assay-normalization.md).
- Prepare and run a reporter assay: [Reporter Run guides](workflow.md), including
  [input preparation](input-preparation.md), the
  [complete run example](complete-command-paths.md), and
  [troubleshooting](reporter/troubleshooting.md).
- Prepare and run a cap assay: [Cap Run guides](cap-selection/workflow.md),
  including [inputs and reference](cap-selection/prepare-inputs.md),
  [Steps 1–3](cap-selection/steps-1-3.md),
  [troubleshooting](cap-selection/troubleshooting.md), and the
  [0.2.0b5 migration guide](cap-selection/migrating-to-0.2.0b5.md).
- Look up commands in the [reporter pipeline CLI](cli/pipe.md),
  [reporter QC CLI](cli/qc.md), [reporter export CLI](cli/export.md), and
  [cap pipeline CLI](cli/cap-assay.md); use the References section for assay-specific
  format contracts, resource guidance, and known limitations.

The [canonical glossary](glossary.md) defines terms shared across pages.
This site preserves the released behavior contract; installed `COMMAND --help`
describes the command surface of the local build. Report a disagreement as a
defect rather than assuming either source changes the other.
