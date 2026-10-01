# Coding agent comparison

A comparison of coding agents and models doing the same task with the
[superpowers](https://github.com/obra/superpowers) plugin. The results will be
presented as a static page, in the style of `../claude-playback`.

## The task

Each run works on its own branch of
[rossturner/stirling-pdf](https://github.com/rossturner/stirling-pdf), a fork of
[Stirling-Tools/Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF),
starting from `main`, and is given this prompt:

> Use the superpowers:brainstorming skill architectural workflow to add a new
> tool to this project under "Page Formatting" of "Coloring book" which should
> accept a set of images, and then produce from those images a PDF where every
> odd-numbered page in the PDF is one of the images as a full page, in sequence,
> and every even-numbered page is a blank page, so that the final PDF produced
> has each image page interleaved with a blank page to be printed on the back of
> it.
>
> Note that project has been set up locally with a username of "admin" and
> password of "password".

## Runs

| Run id | Harness | Model | Effort |
|---|---|---|---|
| `claude-opus-5.5` | Claude Code | Opus 5.5 | medium |
| `claude-haiku-4.5` | Claude Code | Haiku 4.5 | high |
| `codex-sol-6.1` | Codex | GPT Sol 6.1 | medium |
| `codex-luna-6` | Codex | GPT Luna 6 | high |
| `copilot-sol-6.1` | Copilot | GPT Sol 6.1 | medium |
| `copilot-luna-6` | Copilot | GPT Luna 6 | high |
| `atai-copilot-sol-6.1` | ATAI Copilot | GPT Sol 6.1 | medium |
| `atai-copilot-luna-6` | ATAI Copilot | GPT Luna 6 | high |

ATAI Copilot is Copilot with Autotrader AI (ATAI): a set of skills and
instructions that work alongside "vanilla" Copilot.

`data/runs.json` holds each run's status, branch, checkout and the source paths
of its session logs, spec and plan.

## How the runs are conducted

- The brainstorming skill's architectural workflow is used throughout.
- The human answers the agent's questions the same way in every run, generally
  agreeing with its recommendations.
- Where the skill asks for a human review of the written spec, the agent is
  asked to run a subagent as an adversarial reviewer of the spec instead.

## What is captured per run

`runs/<run-id>/`:

- `sessions/` — the raw session JSONL: the main session plus any subagent
  sessions.
- `spec.md` — the design spec written under `docs/superpowers/specs/`.
- `plan.md` — the implementation plan written under `docs/superpowers/plans/`.
- `commits.txt` — commits on the run's branch since `main`.
- `notes.md` — observations made while the run happened, and findings.

Copy these in with:

```
scripts/collect_run.py <run-id>    # or --all
```

It reads `data/runs.json` and can be re-run while a session is still going.
Before collecting a new run, fill in its `branch`, `checkout` and `sessions` in
`data/runs.json`.

Where each harness writes its session logs:

- Claude Code: `~/.claude/projects/<escaped-cwd>/<session-id>.jsonl`, with
  subagents under `<session-id>/subagents/`.
- Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. Subagents get their
  own rollout file whose `session_meta` has a `parent_thread_id` pointing at
  the main session.
- Copilot CLI / ATAI Copilot: `~/.copilot/session-state/<session-id>/`,
  with the event log in `events.jsonl` and the session's cwd and branch in
  `workspace.yaml`. Record the whole directory as the `main` session. Where
  Copilot writes subagent sessions is not known yet.

Codex and Copilot both use the superpowers worktree skill, so
implementation can end up on a different branch in a worktree. Record these
as `implementationBranch` and `worktree` in `data/runs.json`; the collect
script reads the spec, plan and commits from there.
