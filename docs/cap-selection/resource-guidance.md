# Cap assay resource guidance

This guidance covers resources an operator can choose when running the released **0.2.0b4** commands. It does not prescribe scheduler allocations; those belong to the site-specific job setup.

## CPU budgets

Steps 1, 3, and 4 accept positive `--threads` values and default to 16. Step 2 is optional and defaults to 1. Each flag is a per-invocation CPU budget, with stage-specific serial work and worker use described in the [cap CLI reference](../cli/cap-assay.md). Start with the default for a single library, then lower it when running several libraries concurrently or when the host has a smaller CPU allocation. Step 2 gzip compression can be tuned with `--gzip-compression-level` (0 is fastest/largest; 9 is slowest/smallest; default 1).

Step 3 also accepts `--bam-sort-memory` and `--tmp-dir` for samtools sorting. Use a temporary directory with sufficient free space for intermediate sort files. Step 1, 2, and 4 stage outputs under the selected output directory while publishing, so that filesystem needs room for the new outputs and temporary data.

## External tools

| Stage | Operator-installed tools |
| --- | --- |
| Step 1 | `fastp` |
| Step 3 | STAR 2.7.0+, samtools 1.10+, and `zcat` on `PATH` |
| Step 4 | samtools 1.12+, BEDTools 2.30+, and UMI-tools; pyBigWig is installed as a Python dependency |
| Reference preparation | `ExogenousSequenceTools assemble add_adapter`, run externally before Step 3 |

The command references document tool-path overrides where available. CAP alignment has no XP runtime dependency: only the person assembling the external reference needs the relevant sequence-tool environment.

## Output planning

Use a writable output directory with enough room for the selected step's outputs and staging. Avoid running the same library prefix concurrently into the same directory; commands use per-library locks and reject existing output targets rather than overwriting them. Step 4's selected track count depends on `--rna-strand`: four for `both`, two for `plus` or `minus`, plus one JSON summary.
