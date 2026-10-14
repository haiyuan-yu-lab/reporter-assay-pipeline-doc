# Generate cap assay endpoint tracks (Step 4)

Step 4 consumes a compatible coordinate-sorted BAM and publishes strand-selected
cap-signal and polymerase-position proxy tracks. Verify the Step 3 summary
reports success before running it, and repeat the same `--rna-strand` policy
used by Step 3.

```bash
cap-assay-pipeline step4-post-alignment-processing \
  --library-prefix LIB01 \
  --input-bam aligned/LIB01_step3_alignment.bam \
  --rna-strand both \
  --output-dir tracks/
```

With the default `both` policy, Step 4 publishes four bigWigs: `.5pl.bw` and
`.5mn.bw` for R2 cap signal, and `.3pl.bw` and `.3mn.bw` for the R1-derived
polymerase-position proxy. The plus/minus suffixes refer to the
construct-reference-relative biological RNA strand. See [Cap assay
concepts](../cap-assay-concepts.md#two-endpoint-measurements) and the [format
contract](formats.md#step-4-endpoint-bigwigs) for interpretation.

The [cap CLI reference](../cli/cap-assay.md#step4-post-alignment-processing)
defines BAM admission, filtering, dependencies, summary fields, and all
available options.
