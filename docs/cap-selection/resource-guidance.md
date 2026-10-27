# Cap assay resource guidance

This guidance covers resources an operator can choose when running the released **0.2.0b5** commands. It does not prescribe scheduler allocations; those belong to the site-specific job setup.

## CPU budgets

Each `--threads` flag is a positive per-invocation CPU budget. Start with the default for a single library, then lower it when running several libraries concurrently or when the host has a smaller CPU allocation. Scientific results and output ordering do not depend on the budget.

| Step | Default | How the budget is used |
| --- | --- | --- |
| 1 | 16 | Up to `threads - 1` Python worker processes for validation and UMI exclusion, then a separate fastp phase with `-w threads` (fastp may add fixed reader/writer threads) |
| 2 | 1 | Parent reads, merges in order, and publishes; up to `threads - 1` worker processes evaluate bounded chunks of 256 pairs |
| 3 | 16 | Up to `threads` worker threads align ordered batches of 64 pairs; `samtools sort` uses `threads` sorting threads in total; other samtools commands use one thread |
| 4 | 16 | Up to `threads - 1` eligibility workers, `samtools -@ threads-1`, and up to `threads - 1` concurrent BEDTools calls; UMI-tools deduplication and publication are serial |

Step 2 gzip compression of the identified FASTQs can be tuned with `--gzip-compression-level` (0 is fastest/largest; 9 is slowest/smallest; default 1).

## Memory and temporary storage

Step 3 `--bam-sort-memory` (default `2G`) is the aggregate `samtools sort` buffer, divided across its sorting threads; it must provide at least 1 MiB per thread or Step 3 fails before reading pairs. `--tmp-dir` selects an existing writable directory for sort intermediates; use one with enough free space for the accepted alignments.

These budgets bound worker activity and batches, not total process memory. Step 3 holds the complete element FASTA and barcode map in memory, so its footprint scales with those inputs, and each pair's candidate search covers all in-ceiling placements on its selected Element. Longer elements and higher `--max-pair-edits` values increase per-pair work. No speed or memory ceiling is promised.

## External tools

| Stage | Operator-installed tools |
| --- | --- |
| Step 1 | `fastp` |
| Step 2 | None |
| Step 3 | samtools 1.10+ |
| Step 4 | samtools 1.12+, BEDTools 2.30+, and UMI-tools; pyBigWig is installed as a Python dependency |

STAR is not required, and no alignment index is built or stored. The command references document tool-path overrides.

## Output planning

Use a writable output directory with enough room for the selected step's outputs and staging. Steps 1–4 stage outputs under the selected output directory while publishing. Steps 2 and 3 also write rejected-read FASTQs and rejection tables, whose size grows with the number of rejected pairs. Avoid running the same library prefix concurrently into the same directory; commands use per-library locks and reject existing output targets rather than overwriting them. Step 4's selected track count depends on `--rna-strand`: four for `both`, two for `plus` or `minus`, plus one JSON summary.
