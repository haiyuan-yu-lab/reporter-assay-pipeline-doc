# Known limitations in 0.1.0b3

These are limitations of the released build, not instructions to work around
them by guessing at undocumented behavior.

## `fastp` is not version-pinned

Step 1 and `prep_lib` invoke whichever compatible `fastp` executable is selected
or available on `PATH`. Record the external tool version with each run; this
release does not promise equivalent cleaning behavior across `fastp` versions.

## Release validation is unit-test-focused

The code repository has no continuous-integration workflow, and the release was
not validated by rerunning a large end-to-end assay fixture. Contract-level tests
cover the supported command surfaces and artifact behavior.

## Resolved since 0.1.0b2

Release **0.1.0b3** routes every `yulab_reporter_pipe stepN --help` request to
the step-owned parser, resolving [public issue
5](https://github.com/DignoMor/reporter-assay-pipeline/issues/5). It also removes
the ineffective Step 6 `--min-match-length` option; matching remains exact
`ObservedID` to `CanonicalID` lookup, resolving [public issue
6](https://github.com/DignoMor/reporter-assay-pipeline/issues/6).
