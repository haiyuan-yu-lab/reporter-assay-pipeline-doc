# Cap assay troubleshooting

Check each step's summary JSON before using its output in the next stage. Step 1
fails when no pairs remain after preparation or UMI filtering; Step 3 fails when
there are no uniquely mapped pairs; Step 4 fails when no pairs pass its
eligibility filters. For Step 4 strand-contradiction failures, confirm that
the `--rna-strand` value matches the selection used in Step 3.

The [cap CLI reference](../cli/cap-assay.md) defines each stage's failure
conditions and output summary fields. Release-specific scope limits are listed
under [Known limitations](known-limitations.md).
