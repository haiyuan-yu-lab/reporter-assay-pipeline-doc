# Reporter assay normalization

This page describes the released Step 9 behavior in **0.2.0b3**. Step 9
normalizes one reporter branch per invocation: run eBC and pBC separately when
both are present. The [Step 9 guide](steps-9.md) documents commands and output
columns; [format contracts](formats.md#activity-by-element) define the table.

## RNA and DNA are compared within each replicate

For each eligible element and paired replicate, Step 9 compares post-transfection
RNA counts with DNA counts. Its legacy descriptive score is the mean of
`log2((RNA + pseudocount) / (DNA + pseudocount))` across replicate pairs. The
default pseudocount is 1. This `ActivityScore` describes the RNA-to-DNA ratio;
it is not itself the fitted effect used to assign the released activity call.

Step 9 also reports `log2FC`, which subtracts the median legacy `ActivityScore`
of eligible negative controls. `ActivityZ` is centered and scaled by the mean
and population standard deviation of those same legacy control scores. These
descriptive fields keep their established formulas and remain useful summaries
alongside the fitted results.

## Control-guided normalization and fitted calls

For its limma–voom model, Step 9 estimates TMM effective library sizes jointly
across all DNA and RNA libraries in that branch invocation. It derives
M/A-trimming limits from eligible negative controls, then includes eligible
non-controls within those limits when estimating each library's factor. Factors
are recentered to geometric mean one. A comparison needs the configured minimum
number of controls with positive counts in both libraries; unsupported
comparisons fail instead of silently receiving a factor of one.

The model fits RNA-versus-DNA expression using the TMM-adjusted library sizes
and the replicate pairing. With two pairs it uses ordinary voom and fixed pair
effects; with three or more it uses `voomWithQualityWeights` and
`duplicateCorrelation`. The fitted RNA/DNA coefficient is distinct from the
legacy `ActivityScore` because it uses the joint model and normalized library
sizes.

Eligible negative controls establish the fitted baseline: Step 9 takes the
median fitted coefficient among them. For each non-control candidate,
`ControlRelativeLog2FC` is its fitted coefficient minus that median. Its
p-value tests equality with this fixed control median, not a zero RNA/DNA
coefficient. Candidate p-values are adjusted together within that branch
invocation using Benjamini–Hochberg. eBC and pBC do not share a testing family.

The released calls are `Control` for eligible controls, `Active` for a
candidate whose control-relative effect exceeds the positive effect threshold
and whose adjusted p-value passes the cutoff, `Repressive` for the equivalent
negative effect, and `NoCall` otherwise. Default thresholds are an absolute
log2 effect greater than 1 and adjusted p-value at most 0.05. A call describes
the measured relative reporter response under this analysis; it does not by
itself establish a biological mechanism.

## Interpretation, assumptions, and limits

- DNA and RNA input lists must have equal length and pair by list position, with
  at least two biological replicate pairs. File names do not define pairing.
- Elements must meet DNA total-count and detection requirements. Controls and
  candidates use the same eligibility rule, and RNA zeros remain eligible when
  DNA representation passes.
- The analysis universe is the union of elements observed in the input tables;
  absent rows for known elements contribute zero. Malformed input rows fail.
- TMM factors are estimated from observed counts and supported control values.
  The fitted p-values treat normalization factors, the fitted control median,
  and replicated-mode correlation and quality weights as fixed. Their
  estimation uncertainty is not propagated into those p-values.
- The fitted baseline reflects the selected negative-control set and the
  retained analysis space. Controls that fail DNA eligibility cannot define
  that baseline, and Step 9 fails when usable control support is insufficient.
- A zero standard deviation among legacy control `ActivityScore` values leaves
  `ActivityZ` empty with a warning. The fitted model and its calls remain
  separate from this legacy z-score behavior.

For stage-by-stage execution and recovery, see [Call activity (Step 9)](steps-9.md).
