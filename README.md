# Reporter Assay Pipeline — Documentation

Public user-facing documentation for the
[Reporter Assay Pipeline](https://github.com/DignoMor/reporter-assay-pipeline)
**0.2.0b5** (beta).

**Site:** https://haiyuan-yu-lab.github.io/reporter-assay-pipeline-doc/

**Agent index:** https://haiyuan-yu-lab.github.io/reporter-assay-pipeline-doc/llms.txt

This repository publishes six top-level sections: Home, Quickstart, Learn, Run
Reporter Assay Pipeline, Run Cap Assay Pipeline, and References. It is the
source of truth for:

- Quickstart and install guidance
- Workflow overview and library layout
- CLI reference (`yulab_reporter_pipe`, `yulab_reporter_qc`, `yulab_reporter_export`, `cap-assay-pipeline`)
- Assay-specific artifact format descriptions
- Assay-specific troubleshooting and recovery guidance

Native site search is available for exact terms, commands, flags, artifacts,
and symptoms.

Reporter references live under `docs/reporter/` and `docs/cli/`; cap references live under `docs/cap-selection/` and `docs/cli/`.

## Local preview

```bash
pip install -r requirements.txt
mkdocs serve
```

## Related repos

| Role | Repo |
| --- | --- |
| Code (access required) | https://github.com/DignoMor/reporter-assay-pipeline |
| Docs | https://github.com/haiyuan-yu-lab/reporter-assay-pipeline-doc |
