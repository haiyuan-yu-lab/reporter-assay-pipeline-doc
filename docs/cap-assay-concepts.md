# Cap assay concepts

The cap-selection assay measures nascent RNA endpoints from cap-selected
cDNA. It produces endpoint tracks relative to a construct-derived alignment
reference; it does not produce reporter activity tables.

## Reference-relative RNA strand

Plus and minus refer to the biological RNA strand relative to the
construct-derived reference. R1 determines that strand: a forward R1 alignment
means plus, and a reverse alignment means minus. This strand is independent of
the tested element's CW or CCW orientation. The [cap workflow](cap-selection/workflow.md#rna-strand-policy)
explains supported pooling combinations and the operational strand policy.

## Two endpoint measurements

| Measurement | Read source | Biological interpretation |
| --- | --- | --- |
| Cap signal | R2 sequenced 5′ endpoint | Observation of nascent RNA initiation / capped 5′ endpoint |
| Polymerase-position proxy | R1 sequenced 5′ endpoint, assigned to the R1 strand | Pause-biased proxy for the nascent RNA 3′ endpoint |

Step 4 publishes cap signal as `.5pl.bw` / `.5mn.bw` and the polymerase-position
proxy as `.3pl.bw` / `.3mn.bw`. The proxy is not cap signal and is not an
unbiased measure of RNA polymerase II occupancy. Coordinates and signs are
defined by the released [format contract](cap-selection/formats.md#step-4-endpoint-bigwigs).

For commands and input requirements, see [Prepare inputs and reference](cap-selection/prepare-inputs.md)
and the [cap workflow](cap-selection/workflow.md).
