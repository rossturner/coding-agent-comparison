# Copilot — GPT Luna 6 (high)

Status: being re-run.

## Discarded attempt 1

Saved in `discarded-attempt-1/`. Branch `copilot-luna` in
`~/workspace/stirling-pdf-4`, Copilot session `d05eabd3-d8d7-4a25-b26b-34e1e40ec731`,
2026-10-01 20:57 to about 00:25 BST. It finished with 15 commits.

It was discarded because the adversarial spec review ran on claude-haiku-4.5.
Copilot's default model for its `rubber-duck` agent type is a model from
another vendor (`modelSelectionSource: complementary_default`), so the run
wasn't using GPT Luna 6 as specified.

Models chosen by Luna on the 17 `general-purpose` dispatches, following the
superpowers subagent-driven-development "Model Selection" guidance, which is
allowed:

| Time (UTC) | Subagent | Model |
|---|---|---|
| 21:38 | coloring-book-pdf-sequence | gpt-5.4-mini |
| 21:45 | coloring-book-task1-review | gpt-5.4-mini |
| 21:46 | coloring-book-backend-endpoint | gpt-5.4 |
| 21:52 | coloring-book-task2-review | gpt-5.4 |
| 21:54 | coloring-book-task2-fix1 | gpt-5.4 |
| 21:57 | coloring-book-task2-rereview1 | gpt-5.4-mini |
| 21:58 | coloring-book-generated-contracts | gpt-5.4-mini |
| 22:16 | coloring-book-task3-review | gpt-5.4-mini |
| 22:19 | coloring-book-frontend-tool | gpt-5.4 |
| 22:36 | coloring-book-task4-review | gpt-5.4 |
| 22:41 | coloring-book-task4-fix1 | gpt-5.4-mini |
| 22:41 | coloring-book-task4-rereview1 | gpt-5.4-mini |
| 22:43 | coloring-book-quality-gates | gpt-5.4 |
| 22:56 | coloring-book-task5-review | gpt-5.4 |
| 22:59 | coloring-book-final-review | gpt-6-luna |
| 23:08 | coloring-book-final-fix | gpt-5.6-terra |
| 23:21 | coloring-book-final-rereview | gpt-5.4 |

## Setup for the re-run

`~/.copilot/settings.json` now sets `rubber-duck` and `general-purpose`
subagents to `"model": "inherit"` and `"effortLevel": "inherit"`, so their
defaults follow the session model. Explicit model choices made by the agent
still apply.
