# Findings

Findings across runs. The evidence for each is in the run's `notes.md`.

## ATAI Copilot ignored an explicit request to use a subagent

ATAI's instructions forbid subagents "unless explicitly instructed to do so by
the user, or a skill explicitly calls for a subagent". In `atai-copilot-luna-6`
the user did instruct it ("Use a subagent to adversarially review the spec
yourself"). GPT Luna 6 reviewed the spec itself in 16 seconds anyway, and its
reasoning acknowledged that "this doesn't honor the user's request". It later
spawned 8 subagents for subagent-driven development, since a skill called for
them. Vanilla Copilot on the same model and effort did spawn the review
subagent. See `runs/atai-copilot-luna-6/notes.md`.

## Subagent model choice differs by harness

The superpowers subagent-driven-development skill tells the agent to choose
the cheapest model that can handle each subagent's job.

- Claude Opus 5.5 followed it: Haiku and Sonnet for implementation, Sonnet
  for reviews, Opus for the final review.
- Codex Sol 6.1 kept the session model but raised its later subagents to
  `high` effort.
- In Copilot, Luna's first attempt chose gpt-5.4, gpt-5.4-mini and
  gpt-5.6-terra. Copilot also gave its `rubber-duck` reviewer
  claude-haiku-4.5 by default, which is why that attempt was discarded.
- Both Copilot runs that count were made with `modelPolicy: "required"`
  set, so every subagent ran on gpt-6-luna.
