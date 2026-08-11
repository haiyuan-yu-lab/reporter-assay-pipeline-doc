# Known limitations in 0.1.0b2

These are limitations of the released build, not instructions to work around
them by guessing at undocumented behavior. Check the linked public issue for
updates before relying on an affected path.

## Individual-step help is incomplete

Help for some individual pipeline steps does not yet describe the complete
released command surface. Use the documented step pages and contracts while
checking the installed command's help for the local build. Track this defect in
[public issue 5](https://github.com/DignoMor/reporter-assay-pipeline/issues/5).

## Step 6 `--min-match-length` is ineffective

The Step 6 `--min-match-length` option is accepted but does not currently alter
matching behavior as its name suggests. Do not treat it as an effective tuning
control. Track this defect in
[public issue 6](https://github.com/DignoMor/reporter-assay-pipeline/issues/6).

## Ambiguous branch handling is inconsistent

Records that can be interpreted through more than one assay branch are not
handled consistently across the released workflow. Treat ambiguous outcomes as
requiring diagnosis rather than assuming a stable branch-selection rule. Track
this defect in [public issue 7](https://github.com/DignoMor/reporter-assay-pipeline/issues/7).
