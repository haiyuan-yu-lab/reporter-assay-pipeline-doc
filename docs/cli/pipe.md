# `yulab_reporter_pipe`

Pipeline steps and grouped workflows.

```bash
yulab_reporter_pipe --help
```

| Command | Steps | Purpose |
| --- | --- | --- |
| `step1` … `step9` | one each | Individual stages |
| `prep_lib` | 1 → 2 | Trim + delimited records |
| `process_pretrans` | 3 → 4 → 5 | Pre-transfection processing + ID maps |
| `process_posttrans` | 6 → 7 → 8 | One post-transfection replicate |
| `call_activity` | 9 | Activity calling |

> Scaffold page — flag-level detail will be added in a later docs update.
