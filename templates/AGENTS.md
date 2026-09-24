# AGENTS.md (template for a new game repository)

Copy this file into the root of a new game repository and fill in the brackets. Every AI coding
tool should read it before touching code. Keep it short: it is loaded into every session.

## The game

- **Genre and playbook:** [genre], following `playbooks/[genre].md` in rivendale/opensource.
- **One-sentence pitch:** [what the player does and why it is fun].
- **Engine and language:** [engine], [language]. Decided [date]; change it only on purpose.
- **Build and run:** `[command]`. **Tests and playtest script:** `[command]`.

## How we work

1. **Write the ways a change can fail before you write the change.** Then build against that list.
2. **Prove it end to end.** A playtest script or recorded run beats a unit test written by the
   same model that wrote the code.
3. **One vertical slice at a time.** A playable loop first, then systems, then polish.
4. **Ask a second model to review** hard changes: give it the symptom and the code, not your
   diagnosis.

## Borrowed code

- Only from `copy`-class projects in the catalog (permissive licenses).
- Every borrowed file goes into `THIRD_PARTY.md` in the same commit: source, license, what changed.
- GPL or unlicensed code is never pasted into a prompt to be rewritten.

## Secrets and players

- No keys, tokens or passwords in the repository or in prompts; load them from the environment.
- If players can type text that other players or an AI will see, filter it before it is shown.
