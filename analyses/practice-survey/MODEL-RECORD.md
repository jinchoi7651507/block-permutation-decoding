# Models used in the practice survey (recorded 2026-11-02 23:3x KST from the session records)

Source: model identifiers in the session transcript of the agents that did each step (Claude Code subagent records, `message.model`), and `modelUsage` in the JSON outputs of the 2026-11-02 check.

| Step | Date (UTC) | Model |
|---|---|---|
| Search and screening (one agent) | 2026-10-19 20:59 | Claude Opus 5.5 (`claude-opus-5-5`) |
| Coder A, coder B (two agents, run separately) | 2026-10-19 21:32 | Claude Opus 5.5 |
| Resolution of the three disagreements | 2026-10-19 (main session) | Claude Opus 5.5 |
| Audit of 40 automatic exclusions | 2026-10-20 14:00 | Claude Opus 5.5 |
| Second check of the same 40 (`final-check-2026-11-02/`) | 2026-11-02 | Claude Opus 5.5 (`claude -p --model opus`; the CLI also calls Claude Haiku 5.5 for housekeeping) |

Prompts are not distributed.
