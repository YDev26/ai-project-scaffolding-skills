---
name: ai-project-scaffolding
description: Choose, plan, create and validate a minimal root skeleton for a new project using twelve questions. Root scaffolding only; excludes detail scaffolding and routine repository maintenance.
license: Apache-2.0
compatibility: "Mode A: no Python; modes B/C: Python 3.10+; standard library only; Windows/macOS/Linux."
metadata:
  version: "1.0.0"
  distribution: "ai-project-scaffolding-skills"
---

> This document `skills/ai-project-scaffolding/SKILL.md` | Version: v1 | Readers: AI | Purpose: root scaffolding execution skill | Source of truth: references/usage.md (bundled operating contract)
# Create a project root skeleton

Requires this skill directory (`scripts/` + `references/`). Mode A needs no Python; modes B/C need Python 3.10+. For explanations, read the bundled [usage](references/usage.md); this file is the agent execution contract. The repository README is optional project context, not an installation dependency.

Before selecting any mode, resolve the user-specified target to an absolute project path and repeat it in the plan. A named child such as `adopter` means `<cwd>/adopter`, not the current directory or the installed skill directory. Retain that exact target through confirmation, creation and validation.

## Confirm the exact project target before writing

- Resolve the user-specified project path to an absolute path. A named child means `<cwd>/<child>`; never use the installed skill directory as the target.
- If the user supplies an existing nonempty parent/container with other projects but no project directory name, ask for that name and stop before planning a guessed child or creating anything. Do not reuse a name from an earlier target. If it is unclear whether the path is the project itself or its parent, ask which was intended. An explicitly named existing project can be extended after inspection and confirmation.
- Present the exact target, tier, complete visible/hidden entries, existing-entry conflicts and defaults. Wait for a subsequent user reply approving that plan. A prior “do it” for another target does not authorize it; changing the parent, child name, tier or entry list requires a fresh plan and confirmation. Permission settings do not substitute for this checkpoint.
- Keep planning and creation in separate tool calls with the user confirmation between them; never batch `--plan` and `--apply` in one tool call or execute both before showing the plan. Apply and validate the same confirmed absolute target. Reinspect existing entries before writing; if they changed since the plan, stop and present an updated plan.
- The generator uses fixed slot names. `pyproject.toml` is an empty placeholder, and the default `.gitignore` includes Python patterns; neither selects the project's language. Explain these defaults before confirmation. For a different build anchor, agree on a manual plan rather than silently creating both anchors or claiming automatic slot substitution.



## Choose a mode

| Mode | Requires | What it does | Completion evidence |
|---|---|---|---|
| A Manual fallback | Nothing | Follow [root items](references/root-items.md) and create entries by hand | Manual checklist; **no gate exit code**; say "gate not run" |
| B Bundled script (recommended) | Python 3.10+ | `scripts/standard.py tier --plan/--apply` plus `check-root` | `check-root` exit 0 |
| C Installed CLI | Python 3.10+ and the CLI installed from the full distribution repository | `ai-project-scaffold tier` plus `check-root` | `check-root` exit 0 |

Never claim the root gate passed in mode A. Do not mix completion criteria across modes. C is a deployment variant of B: same capability and completion evidence, different install. The five steps below are modes B/C; in mode A use [root items](references/root-items.md), include the default hidden entries (.gitignore, .gitattributes, .github/), and skip the gate. A plan-only request must stop before writing in every mode.

Select a command prefix once and retain it for every step:
- B: `python "<skill-dir>/scripts/standard.py"`, where `<skill-dir>` is the absolute directory containing this SKILL.md. It works from any current directory.
- C: `ai-project-scaffold`, from the active environment where it is installed. To install, run `python -m pip install "<distribution-repo>"` with the absolute full-repository path containing pyproject.toml; a copied skill directory cannot be pip-installed. If only this skill directory is available, use B.

Append the subcommands below to that prefix; `<target>` is the explicit adopter project path.

1. Establish the project's purpose, users and deliverables from the user's request and repository context. Run `tier --list --json` with the selected prefix. Answer all twelve questions with Yes/No and evidence; count only current needs or needs certain within three months. Default to the smallest tier.
2. Pass matched IDs with repeated `--trigger` arguments to `tier --plan --json --root "<target>"`. Present the tier, target, visible and hidden entries; obtain human confirmation before writing.
3. With the same triggers and target, run `tier --apply --json --root "<target>"`. Before any write, obtain user permission; before any overwrite-prone operation, ask whether a backup exists and whether it can be rolled back. Preserve nonempty files. Empty hidden configs may receive defaults; preflight conflicts cause no writes; later I/O failures can leave partial creation without rollback. Inspect errors before retrying.
4. Read the returned tier and run `check-root --tier <small|medium|large> --root "<target>" --json`. Report commands, exit codes, created/skipped entries and errors in the user's language. Exit codes: 0 success, 1 operation or validation failure, 2 usage error.
5. Stop after root validation. This skill creates the root skeleton only; detail scaffolding, document contents and detail gates come later. Root validation does not approve content or publication.

References: [root items](references/root-items.md), [safety](references/safety.md), [usage](references/usage.md). For operating-rule ambiguity, consult the bundled Chinese [usage](references/usage.md); root items and safety summarize it. The full repository README.zh-CN.md governs project context when available, but is not required to execute an installed skill. Install via the plugin marketplace, `npx skills add`, or copy this skill directory to `.claude/skills/` or `.agents/skills/`.
