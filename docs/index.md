# Reporter Assay Pipeline

This site documents release **0.2.0b3** of the Reporter Assay Pipeline. Choose
the assay that matches your data: the reporter assay measures element-level
activity from RNA and DNA counts; the cap assay produces strand-selected
nascent RNA endpoint tracks.

## Choose an assay

- **Reporter assay:** start with the [reporter workflow](workflow.md) to prepare
  paired-end libraries and run the nine-step activity analysis. See
  [reporter assay concepts](reporter-assay-concepts.md) for PreTran, PostTran,
  branches, and identifiers.
- **Cap assay:** start with the [cap workflow](cap-selection/workflow.md) to
  prepare and align reads and generate endpoint tracks. See
  [cap assay concepts](cap-assay-concepts.md) for reference-relative RNA strand
  and the two endpoint measurements.

## Find guidance by task

- First installation: [Quickstart](quickstart.md).
- Understand how the assays relate: [Assay overview](assay-model.md).
- Understand reporter normalization: [Reporter assay normalization](reporter-assay-normalization.md).
- Prepare and run a reporter assay: [Reporter Run guides](workflow.md), including
  [input preparation](input-preparation.md) and the
  [complete run example](complete-command-paths.md).
- Prepare and run a cap assay: [Cap Run guides](cap-selection/workflow.md),
  including [inputs and reference](cap-selection/prepare-inputs.md) and
  [Steps 1–3](cap-selection/steps-1-3.md) and
  [troubleshooting](cap-selection/troubleshooting.md).
- Look up commands in the [reporter pipeline CLI](cli/pipe.md),
  [reporter QC CLI](cli/qc.md), [reporter export CLI](cli/export.md), and
  [cap pipeline CLI](cli/cap-assay.md); use the References section for format
  contracts, resource guidance, and known limitations.

The [canonical glossary](glossary.md) defines terms shared across pages.
This site preserves the released behavior contract; installed `COMMAND --help`
describes the command surface of the local build. Report a disagreement as a
defect rather than assuming either source changes the other.
