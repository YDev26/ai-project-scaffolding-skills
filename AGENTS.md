> This document `AGENTS.md` | Version: v1 | Readers: both | Purpose: working contract for AI and developers | Source of truth: README.zh-CN.md
# AGENTS | V1 working agreement

Read this file -> [Chinese README: source of truth](README.zh-CN.md) -> task-relevant documents. The root [README](README.md) is an English display copy, not a rule authority. Read only what the task needs.

- V1 is root-only: tier selection, root planning, creation and validation. Detail scaffolding comes later.
- Write AGENTS and SKILL in concise English. Keep explanations, truth documents and code comments in Chinese. Identifiers, paths and protocol keys are English. Language does not change authority; resolve conflicts against the Chinese truth source. Reply to users in their requested language.
- Keep execution instructions self-contained. Do not add parallel translations or load explanatory references unless needed for the task.
- The functional core is in `skills/ai-project-scaffolding/scripts/`; `tests/` supports verification. Creation and gates must share the same tier data. Update the contract, explanations and relevant counterexamples together.
- Bind adopter approval to the exact absolute target and complete plan. An ambiguous project container needs a project name first; changed targets/plans need fresh confirmation. Show the plan, wait for a user reply, then apply in a separate call.
- Create missing entries and preserve nonempty files. Zero-byte .gitignore / .gitattributes may receive defaults. Creation may partially succeed; do not promise rollback.
- Before any write, obtain user permission; before any overwrite-prone operation, ask whether a backup exists and whether it can be rolled back.
- Do not read/write credentials or delete, move or rename human-created content without authorization. Publication needs explicit user authorization.
- Run `python tests/run_tests.py`. Validate adopters with `python skills/ai-project-scaffolding/scripts/standard.py check-root --tier <small|medium|large> --root <target> --json`. Report commands, exit codes and unfinished work.
