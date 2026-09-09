# Prepare inputs

Use this page before running `prep_lib`, `process_pretrans`,
`process_pretrans_cw_only`, `process_posttrans`, or `call_activity`. It is the
input-readiness contract for release **0.1.0b3**. Check every item before
starting a library; a failure in one required input should stop that library
or workflow rather than being treated as a low read-retention result.

## Readiness procedure

1. Choose the workflow profile: dual-orientation/dual-branch, CW-only/eBC, or
   another explicitly supported subset.
2. Assign a unique canonical library prefix to each input and keep the same
   prefix in the R1 filename, R2 filename, schema, summary, and downstream
   command.
3. Validate each raw pair below, then validate the reference, control, and
   schema assets.
4. Run the valid next command shown for that input class. If a check fails,
   stop and correct the asset; do not continue with a partial handoff.

## Library sets and filenames

The complete profile contains these symbolic library prefixes. `N` is the same
replicate count for each DNA/RNA condition.

| Set | Required prefixes | Canonical example pair |
| --- | --- | --- |
| PreTran | `PreTran_CW`, `PreTran_CCW` | `PreTran_CW_R1.fastq.gz`, `PreTran_CW_R2.fastq.gz` |
| eBC DNA | `eBC_DNA_rep1` … `eBC_DNA_repN` | `eBC_DNA_rep1_R1.fastq.gz`, `eBC_DNA_rep1_R2.fastq.gz` |
| eBC RNA | `eBC_RNA_rep1` … `eBC_RNA_repN` | `eBC_RNA_rep1_R1.fastq.gz`, `eBC_RNA_rep1_R2.fastq.gz` |
| pBC DNA | `pBC_DNA_rep1` … `pBC_DNA_repN` | `pBC_DNA_rep1_R1.fastq.gz`, `pBC_DNA_rep1_R2.fastq.gz` |
| pBC RNA | `pBC_RNA_rep1` … `pBC_RNA_repN` | `pBC_RNA_rep1_R1.fastq.gz`, `pBC_RNA_rep1_R2.fastq.gz` |

These names are examples, not required filesystem paths. Do not substitute
branch names for identifier names: `eBC` is a branch and `EID` is its
identifier domain; `pBC` is a branch and `PID` is its identifier domain.

### Profile variations

- A dual-orientation PreTran set has both `PreTran_CW` and `PreTran_CCW` and
  uses forward and reverse references respectively. The ordinary dual-ID
  profile declares `EID,PID`.
- A CW-only/eBC set has `PreTran_CW`, one forward reference, and the eBC
  post-transfection DNA/RNA replicates. Its PreTran profile may declare only
  `EID`; it does not produce a PID cluster reference or pBC activity table.
- Do not invent a missing orientation or branch. If the intended profile is
  not one of these documented variations, stop and confirm its support before
  preparing files.

## Paired FASTQ checks

For every library, R1 and R2 must be readable, non-empty, gzip-valid FASTQ
files. They must have the same number of records and preserve pair order. A
pair is not ready if either file is truncated, contains incomplete four-line
records, fails gzip decompression, or has a different record count from its
mate. R1/R2 direction is part of the contract; do not swap the files merely
because a downstream field appears in the other read.

Use a read-only check appropriate to your environment before invoking the
pipeline. For example, these commands inspect compression and record counts
without changing the input files:

```bash
gzip -t "<raw_dir>/eBC_DNA_rep1_R1.fastq.gz"
gzip -t "<raw_dir>/eBC_DNA_rep1_R2.fastq.gz"
zcat "<raw_dir>/eBC_DNA_rep1_R1.fastq.gz" | awk 'END { print NR / 4 }'
zcat "<raw_dir>/eBC_DNA_rep1_R2.fastq.gz" | awk 'END { print NR / 4 }'
```

The two counts must be equal and non-zero. Also inspect the first record names
when the producer supplies pair suffixes; R1 and R2 names should identify the
same pair. A valid check leads to `prep_lib` with the pair as `--input-r1` and
`--input-r2`. A failed check stops execution until the pair is regenerated or
repaired; do not rely on Step 1 to repair synchronization or gzip corruption.

After `prep_lib`, verify the trimmed R1/R2 outputs and the Step 1 summary. The
summary must report `status: success`, and the output pair counts must remain
synchronized. The next valid command is Step 2 (or the corresponding grouped
PreTran/PostTran command) using those retained trimmed files.

For complete individual commands, artifact contracts, and recovery guidance,
see [Steps 1–2: prepare one library](steps-1-2.md).

## Layout schemas

Every library passed to Step 2 needs a JSON layout schema. The schema must
contain `layout1`, `layout2`, and ordered `column_names`; see [Layout schema
reference](layout-schemas.md). `reverse_complements`, when present, may name
only fields in `column_names`.

Do not reuse a schema across library types unless its read layout and output
fields are actually identical. A schema/header mismatch is configuration-fatal
before extraction. A row-level anchor mismatch is tolerated and counted, but a
run with no retained records fails.

## Reference FASTA checks

For each supplied reference:

- It must be readable, parseable FASTA with a non-empty sequence payload for
  every record.
- Every record header (the `Element` value) must be unique within that file.
- Sequence keys must not be ambiguous: duplicate reference sequence keys are
  invalid for orientation matching.
- In a dual-orientation set, the forward and reverse files must contain the
  same number of records. Record position `i` in the forward file pairs with
  record position `i` in the reverse file; headers do not establish pairing.
- `PreTran_CW` uses the forward reference and `PreTran_CCW` uses the reverse
  reference. A CW-only run needs only the forward reference.

The next valid command after reference validation is the matching PreTran
workflow or Step 3 invocation with one orientation-appropriate `--reference`.
Stop if a FASTA is malformed, headers repeat, record counts differ, or the
orientation assignment is uncertain. Step 3 may skip unmatched rows, but it
must not be used to conceal a bad reference asset.

## Negative-control list

The negative-control annotation is a plain UTF-8 text file with one `Element`
identifier per non-empty line. It has no header. Blank lines are ignored.
IDs must use the same namespace as the Step 8 element-count tables and must be
retained in the shared intersection of all Step 9 DNA/RNA replicates.

```text
CTRL_SYMBOLIC_A
CTRL_SYMBOLIC_B
```

The list must be readable and non-empty. The valid next command is
`call_activity` (or export where its control argument is required). Stop if
the list is empty or none of its IDs survive replicate alignment; Step 9
cannot compute a negative-control baseline in that case.

## Final checklist

- Every required library has exactly one R1/R2 pair with matching, non-zero
  record counts.
- R1 and R2 are gzip-valid, readable, and named consistently.
- The selected profile's branch, orientation, and replicate set are explicit.
- Each library has the correct layout schema and output-column contract.
- Forward/reverse FASTA files are unique, non-empty, equally sized, and
  positionally paired when both are required.
- The negative-control list is non-empty and uses retained `Element` IDs.
- All examples and paths remain generic; replace placeholders only in your
  local command line.

See [Workflow](workflow.md) for stage handoffs and [Artifact formats](formats.md)
for exact downstream table headers.
