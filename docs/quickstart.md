# Quickstart

This page documents release **0.2.0b5**. Install the package and verify its
four command-line entry points, then continue to the Run guide for your assay.

## Requirements

- Python 3.9 or newer.
- `fastp` on `PATH` for reporter library preparation and cap Step 1.
- Cap Step 3 requires samtools 1.10+; cap Step 4 requires samtools 1.12+,
  BEDTools 2.30+, and UMI-tools. STAR is not required. See the
  [cap CLI dependencies](cli/cap-assay.md#installation-dependencies).

## Install

With access to the private GitHub repository and SSH credentials configured:

```bash
pip install git+ssh://git@github.com/DignoMor/reporter-assay-pipeline.git@0.2.0b5
```

Or install from a local checkout of the `0.2.0b5` tag or matching commit:

```bash
pip install .
```

Install `fastp` separately before using library preparation. The pinned package
release and this site together describe the released operator contract.

## Verify

```bash
yulab_reporter_pipe --help
yulab_reporter_qc --help
yulab_reporter_export --help
cap-assay-pipeline --help
```

Continue with [Run Reporter Assay Pipeline](workflow.md) or
[Run Cap Assay Pipeline](cap-selection/workflow.md) to prepare inputs and run
the appropriate assay. Cap assay users upgrading from an earlier release
should first read [Migrating to 0.2.0b5](cap-selection/migrating-to-0.2.0b5.md);
earlier cap outputs must be regenerated.
