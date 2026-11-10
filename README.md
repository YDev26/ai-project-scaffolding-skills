> This document `README.md` | Version: v1 | Readers: both | Purpose: English display copy and quick start | Source of truth: README.zh-CN.md
# ai-project-scaffolding-skills | Root Skeleton V1

[English](README.md)-display only. | [中文(真相源 / authoritative)](README.zh-CN.md)-governs scope and rules.

Select the smallest useful root layout: twelve questions -> tier -> exact target and plan -> human confirmation -> create -> root gate -> validate.

Python 3.10+; no runtime dependencies. V1 ships root scaffolding only; detail scaffolding starts in V2.

## Install

- Claude Code plugin marketplace: `/plugin marketplace add https://github.com/YDev26/ai-project-scaffolding-skills.git` then `/plugin install ai-project-scaffolding@ai-project-scaffolding-skills`.
- Skills CLI: `npx skills add https://github.com/YDev26/ai-project-scaffolding-skills.git --skill ai-project-scaffolding`.
- Manual: copy `skills/ai-project-scaffolding/` to `~/.claude/skills/` or `.agents/skills/`.
- Optional CLI: `python -m pip install "<distribution-repo>"` exposes `ai-project-scaffold` in that Python environment. The path must be the full repository containing pyproject.toml; `pip install .` works only from that repository root. A copied skill directory uses mode B without package installation.

The public repository is [https://github.com/YDev26/ai-project-scaffolding-skills](https://github.com/YDev26/ai-project-scaffolding-skills). For a local checkout, use `npx skills add "<distribution-repo>" --skill ai-project-scaffolding` or copy the skill directory.

## Modes

| Mode | Requires | Completion evidence |
|---|---|---|
| A Manual fallback | Nothing | Manual checklist; **no gate exit code** |
| B Bundled script (recommended) | Python 3.10+ | `check-root` exit 0 |
| C Installed CLI | Python 3.10+ and `pip install .` | `check-root` exit 0 |

Mode A must say "gate not run"; never claim the gate passed. The commands below use B. For C, replace `python skills/ai-project-scaffolding/scripts/standard.py` with `ai-project-scaffold` after installation.

## Project users

Run from this repository without installation:

```bash
python skills/ai-project-scaffolding/scripts/standard.py tier --list
python skills/ai-project-scaffolding/scripts/standard.py tier --trigger public --plan --root ../my-project
```

Show the plan and wait for user confirmation before running:

```bash
python skills/ai-project-scaffolding/scripts/standard.py tier --trigger public --apply --root ../my-project
python skills/ai-project-scaffolding/scripts/standard.py check-root --tier medium --root ../my-project --json
python skills/ai-project-scaffolding/scripts/standard.py human --root ../my-project
```

- `human` is the interactive path for people; agents use `tier --plan/--apply` plus `check-root`.
- Confirm the exact absolute target and complete plan; ask for a project name when a container path is ambiguous. Changed targets or plans need fresh confirmation.
- Review the plan before --apply; the `human` wizard requires yes. Use --apply --dry --json for a preview.
- Existing nonempty files are preserved. Empty .gitignore / .gitattributes may receive defaults.
- Preflight conflicts cause no writes; later I/O failures can leave partial creation without rollback. Fill adopter document and license contents yourself.
- For AI use, load [SKILL.md](skills/ai-project-scaffolding/SKILL.md). It contains the root workflow. Installed skills use their absolute `<skill-dir>/scripts/standard.py` path; the bundled [usage](skills/ai-project-scaffolding/references/usage.md) includes commands that work outside this repository.

## Developers and reviewers

- Read [AGENTS](AGENTS.md) -> [Chinese README](README.zh-CN.md) -> the relevant document.
- [Usage](skills/ai-project-scaffolding/references/usage.md), [root items](skills/ai-project-scaffolding/references/root-items.md) and [safety](skills/ai-project-scaffolding/references/safety.md) are explanations for human review.
- AGENTS and SKILL are English execution instructions; comments and truth documents are Chinese.
- CLI and JSON default to English; Chinese input aliases remain accepted. No duplicate translation fields are emitted.
- Run `python scripts/check_evals.py --run-plans` and, after installation, `python tests/run_tests.py --installed-cli ai-project-scaffold`.

License: [Apache-2.0](LICENSE).
