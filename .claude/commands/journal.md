---
description: Draft and log a journal entry from recent conversation context
allowed-tools: Bash(journal *)
---

Look back at the recent conversation and identify what just happened that's
worth logging — a bug found and fixed, a decision made, something learned,
a milestone reached, or an open question. If the user gave a hint after the
command ($ARGUMENTS), use it to focus on the right moment instead of
guessing.

Draft:
- `raw_note`: a concise, accurate summary in your own words — grounded only
  in what actually happened in this conversation, not invented detail.
- `entry_type`: one of note, decision, bug, milestone, learning, question.

Show the user both, and ask them to confirm, edit, or cancel. Do not run
anything yet.

Only after the user explicitly confirms, run:
journal log "<raw_note>" --type <entry_type>

If the user asks for edits, redraft and ask again. If they cancel, do
nothing further.
