# Opt-in bounded PR reviewer

The workflow compares `AI_REDTEAM_ENABLED` with `true` using GitHub
[case-insensitive string equality](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#operators).
`TRUE` or mixed case can start the job, but the pinned Python script accepts only lowercase `true`
and returns before reading either credential otherwise. Set lowercase `true` to run a review.
Unset or false skips the secret-bearing job. Forks, foreign repositories and Dependabot skip too.
It checks out the server-supplied base SHA, then the reviewer at a full reviewed commit. PR head code,
install scripts and dependencies never execute with the model key. Git credentials are not persisted.
The token is read-only; results appear only in the Actions summary. There are no comment writes.

Reviewer source: `rivendale/ai-redteam` commit `682e67dd0722ec59ca20843eead86a4857e03ad6`.
Independent correction read: https://github.com/rivendale/ai-redteam/pull/93#issuecomment-6330983394.
The pin includes safe diagnostics. Later OSV work is a separate candidate and is not implicitly followed.
The workflow never uses the reviewer's main branch. A pin change needs a fresh boundary read.

After independent review, the owner sets the explicit `AI_REDTEAM_MODEL` variable and enables
`AI_REDTEAM_ENABLED` after the operator sets `AI_REDTEAM_MODEL_KEY`. This build changes no repository
variable or secret. Enabling is an owner operation. One round is an input to independent review,
never an approval or merge recommendation.

Run `python3 tests/ai-redteam-review/check.py --source /path/to/reviewed/ai-redteam`.
The source must have the exact reviewed tree. The local test evaluates the actual workflow expression
for eligible lowercase and uppercase values, disabled/unset variables, forks and Dependabot.
Separate script tripwires prove uppercase values return before credential access or transport. It then runs the pinned source's
secret-access tripwire and diagnostic tests. The separate offline CI job has no model key and repeats
these checks. It checks out the PR for testing only in that key-free job.
