# AI Capability Evaluator 0.4.0

Entry: `SKILL.md`. This directory is the complete installable Agent Skill; keep its references, scripts and assets together. Python scripts require Python 3.10+ and the standard library only.

Install with the standard Skills CLI (Node.js 22.20+ and Git):

```bash
npx skills add 1085995907ljh-hash/ailevel-judgement --skill ai-capability-evaluator
```

To select Codex and Claude Code globally, append `-a codex claude-code -g`. Manage it with `npx skills list -g`, `npx skills update ai-capability-evaluator -g`, and `npx skills remove ai-capability-evaluator -g`. Omit `-g` for project installations. The npm package is the shared `skills` installer; this Skill is distributed from GitHub.

If the new skill is not visible, restart the session. Invoke `$ai-capability-evaluator` in Codex or `/ai-capability-evaluator` in Claude Code. Other hosts can read `SKILL.md` directly. See `references/platforms.md` for manual fallback, fresh-context requirements and display fallback.

The workflow processes one candidate at a time, always assigns one of five levels, and creates a separate two-section HTML report. There is no independent audit. Inaccessible or insufficient material yields an explicitly provisional Assisted grade, low confidence and disclosed gaps, never invented evidence. Fresh scoring infrastructure must actually be available.

Read `references/rubric.md` for the adapted rubric 1.1 and `references/output-contract.md` for schema 2.0. The original reference image includes a universal error-catching veto; this workflow intentionally removes that veto while retaining L2's own automatic-error-detection criterion. Report UI has no four-dimension table.

Run checks:
```bash
python3 -m unittest discover -s <skill>/tests -v
python3 <skill>/scripts/report.py validate <skill>/assets/example-report.json
python3 <skill>/scripts/report.py render <skill>/assets/example-report.json --output <scratch>/demo.html
```

`input_files`: synthetic file-backed fixture in `assets/example-report.json` and `evals/cases/`. This demo is authored, not an actual scoring invocation. Never place real candidate data in the skill. Source extraction requires host-provided tools; the scripts inventory and render only.

owner and review cadence: repository maintainer, per release. output contract: `references/output-contract.md`. rollback boundary: restore the prior installed skill; preserve candidate materials and historical outputs independently. Script execution remains subject to the current task and host permissions; metadata does not grant future permission.

Verification, trust report and missing evidence: `reports/verification.md`. Repository: https://github.com/1085995907ljh-hash/ailevel-judgement
