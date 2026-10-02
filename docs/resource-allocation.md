# CPU and resource allocation

`--threads` is the CPU budget for one invocation. Existing defaults are
preserved: CAP Steps 1, 3, and 4 and Reporter Steps 1 and 2 default to `16`;
new standalone budgets default to `1`. A budget limits concurrent CPU work; it
does not require every phase to use every slot. `--threads 1` uses the direct
serial path wherever Python workers are supported.

| Surface | Budget and parallel work | Serial phases and state that can grow |
| --- | --- | --- |
| CAP Step 1 — FASTQ preparation | Default `16`. Bounded Python pair validation and UMI exclusion use at most `threads - 1` workers plus the parent; fastp receives the selected value as `-w` in its separate phase. CI limits concurrent libraries with `PREP_LIBRARY_WORKERS`. | Gzip traversal, paired ordered publication and summary reduction are parent-owned. fastp can create fixed reader/writer activity outside `-w`; its per-process memory is separate from bounded Python buffers. |
| CAP Step 2 — optional clipping | Default `1`. Bounded pair-local clipping workers use at most `threads - 1` worker processes plus the parent. CI divides `THREADS` among libraries and caps simultaneous clipping with `CLIP_LIBRARY_WORKERS` (Slurm default `4`; direct harness default `2`). | Input traversal, ordered paired output, histogram reduction and publication are serial. Direct harness concurrency defaults to two libraries; Slurm is bounded by the same clipping ceiling and available CPUs. |
| CAP Step 3 — alignment | Default `16`. STAR index and alignment phases each receive `--threads` and run separately. Complete QNAME-group BAM work uses at most `threads - 1` workers plus the parent. Independent CI libraries split the shared allocation. | FASTQ admission, global FASTA-uniqueness validation, coordinate sorting, reduction and publication are serial. samtools uses its default single thread; STAR's separate `zcat` reader is fixed activity outside `--runThreadN`. Reference and alignment evidence scale with their input cardinalities. |
| CAP Step 4 — endpoint tracks | Default `16`. Complete QNAME-group eligibility work is bounded and parallel; samtools `-@` receives at most `threads - 1` additional threads. Independent BEDTools calls share the remaining invocation budget. CI divides its allocation among concurrent libraries. | UMI-tools deduplication is one global operation per library. Endpoint normalization, track construction, global reconciliation and publication remain serial. |
| Reporter Step 1 — FASTQ preparation | Existing default `16`; fastp receives the selected worker count. `prep_lib` reuses the same budget sequentially for Step 1 then Step 2. CI schedules independent preparation jobs within its stage ceiling. | Input/output checks and handoff ordering remain barriers. fastp may have fixed auxiliary activity; keep its memory cost in the library concurrency decision. |
| Reporter Step 2 — record extraction | Existing default `16`; the parent synchronizes mates and merges ordered bounded chunks from at most `threads - 1` workers. `prep_lib` reuses the Step 1 budget after Step 1 completes. | Mate traversal and ordered publication are serial. Queue and per-worker records are bounded independently of input length. |
| Reporter Step 3 — orientation matching | Default `1`; bounded row chunks use at most `threads - 1` workers and worker-local read-only references. With grouped `process_pretrans`, a budget above one runs CW and CCW concurrently with deterministic child budgets `ceil(B/2)` and `floor(B/2)`; `B=16` gives `8+8`. | Ordered output and counter reduction remain parent-owned. Step 4 waits for both orientations; Steps 4 and 5 then reuse the full group budget sequentially. CW-only uses the full budget for its one orientation. |
| Reporter Step 4 — PreTran aggregation | Default `1`; bounded chunks produce partial molecule contributions with ordered global reconciliation. | Molecule identity, ambiguity resolution and final count ordering remain global. In grouped PreTran, Step 4 starts after all required Step 3 work and reuses the selected budget. |
| Reporter Step 5 — ID maps | Default `1`; independent ID domains and bounded candidate-comparison partitions use worker processes. | All candidate edges are merged before global connected components, canonical-support/tie choices, cross-domain consistency and publication. Graph and map state scale with identifier cardinality. |
| Reporter Steps 6–8 — PostTran | Each standalone step and `process_posttrans` default to `1`. Steps 6, 7, and 8 reuse one selected grouped budget sequentially. Independent library invocations share the Reporter CI stage allocation. | Ordered table publication is parent-owned. Step 7's unique-molecule set/count map, Step 8's element totals and Step 6's reference map scale with distinct keys; their queues remain bounded. |
| Reporter Step 9 — activity | Default `1`; independent DNA/RNA count tables load in input order with at most `threads - 1` workers. CI can divide its stage budget among independent branches. | One global eligibility set, normalization, paired model, retained-control baseline and BH family remain per invocation. Common R/BLAS environment controls are best-effort; a backend may ignore unsupported settings. Count maps and the joint matrix scale with observed elements. |
| Reporter QC | `--threads` defaults to `1` for between-replicate and orientation plotting commands; those commands prepare independent source tables with bounded workers. Other single-source plot commands remain serial and expose no worker flag. | Each Matplotlib render/publication remains in one process; global joins and reductions preserve plot meaning. |
| ExogeneousSequences export | Default `1`; independent reference FASTAs can be prepared by bounded workers. | Global reference disjointness checks, activity joins, ordering and final publication are parent-owned. Multi-file publication is staged and rolled back together on failure. |
| Reporter Step 2 concatenation | No `--threads` option. Each `concat_step2_records` invocation streams gzip inputs in argument order to one gzip output; the Reporter harness invokes one concat at a time inside its library dependency loop. | The concatenated rows are not partitioned, reordered, deduplicated or transformed. Independent invocations have no worker selector; do not count them as parallel support unless a future scheduler explicitly budgets them. |
| CAP external reference prerequisite | No CAP CPU flag is passed to `ExogenousSequenceTools assemble add_adapter`; its public help exposes no thread selector. The tracked CAP CI runs one reference stage after optional Step 2 and before Step 3, outside concurrent processing stages. | Tool-internal CPU and memory use are not controlled or reported by CAP. The stage's command, status and elapsed time are logged, and the Slurm CPU allocation is recorded in run provenance. Keep XP tools outside the CAP runtime dependencies; alignment accepts compatible standalone FASTA. |

## Tracked CI allocations

CAP Slurm CI defaults to 32 CPUs and 128 GiB. That job sets
`PREP_LIBRARY_WORKERS` and `CLIP_LIBRARY_WORKERS` to 4, so preparation, optional
clipping, alignment, and post-alignment each run up to four libraries with eight
CPUs per invocation. Direct CAP harness defaults remain conservative: one
preparation library and two clipping libraries. Operators who override the job
to a smaller memory allocation must lower those ceilings; four concurrent
`fastp` instances are not safe at 32 GiB.

Reporter Slurm CI takes `THREADS` from `SLURM_CPUS_PER_TASK` and retains its
existing 32 GiB memory allocation. `REPORTER_PREP_CONCURRENCY`,
`REPORTER_POSTTRAN_CONCURRENCY`, and `REPORTER_ACTIVITY_CONCURRENCY` each default
to `2`; each caps simultaneous tasks for preparation, PostTran, and activity,
respectively. The scheduler further caps effective concurrency by `THREADS`
and the task count, and divides the parent budget deterministically among
concurrent children so their budgets sum to no more than the allocation. At
budget `1`, independent calls run serially. With `THREADS=16` and the default
stage cap, two concurrent child invocations receive eight CPUs each; bounded
workers and native tool flags remain inside each child's share. Stages wait for
their required predecessors and fail the workflow if a child fails.

Resource summaries report configured/effective workers, tool threads, queue
bounds, observed work and serial-phase reasons where the stage contract defines
them. Natural-cardinality maps, deduplication state and activity matrices are
reported separately from bounded task buffers. These controls establish
bounded allocation and scientific parity; they do not promise a fixed
wall-clock speedup.
