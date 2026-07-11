# Quickstart

## Requirements

- Python 3.9 or newer
- `fastp` on `PATH` for Step 1 / `prep_lib` (not version-pinned; whatever binary is on `PATH` is used)
- Core Python dependencies are declared in the code package `pyproject.toml` (`edlib`, `matplotlib`, `numpy`, `pandas`) and install with the package

## Install

From the public GitHub repository:

```bash
pip install git+https://github.com/haiyuan-yu-lab/reporter-assay-pipeline.git
```

Or from a local checkout of a `0.1.0b1` tag or matching commit:

```bash
pip install .
```

Install `fastp` separately before running Step 1 or `prep_lib`.

## Verify

```bash
yulab_reporter_pipe --help
yulab_reporter_qc --help
yulab_reporter_export --help
```

## Required inputs

Prepare these before a full run:

- Raw paired FASTQ files (`R1` / `R2`) for each pre-transfection and post-transfection library
- Layout schema JSON files that describe how Step 2 parses barcode and anchor fields
- Forward- and reverse-orientation tested-library reference FASTA files (see [Workflow](workflow.md)#forwardreverse-reference-pairing)
- A negative-control annotation file (one element ID per non-empty line)

Default intermediates and outputs are written under `<project_dir>/work/` unless you set `--project-dir` or `--output-dir`.

## Library layout

The standard experiment layout expects `2 + 4 × N` libraries, where `N` is the number of post-transfection replicates per material and branch.

| Group | Library prefixes | Count |
| --- | --- | --- |
| Pre-transfection | `PreTran_CW`, `PreTran_CCW` | 2 |
| Post-transfection eBC | `eBC_DNA_rep1` … `eBC_DNA_repN`, `eBC_RNA_rep1` … `eBC_RNA_repN` | `2N` |
| Post-transfection pBC | `pBC_DNA_rep1` … `pBC_DNA_repN`, `pBC_RNA_rep1` … `pBC_RNA_repN` | `2N` |

## Next steps

- [Workflow](workflow.md) — stages, default paths, and success criteria
- [CLI overview](cli/index.md) — the three installed commands
- [Pipeline CLI](cli/pipe.md) — end-to-end grouped-command example
