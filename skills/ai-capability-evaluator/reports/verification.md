# Release verification — 0.4.0

Publication target: `skills/ai-capability-evaluator`; identity: `ai-capability-evaluator`. The Yao engine and private candidate runs are outside this release. This is a public experimental library package, not a claim of calibrated hiring accuracy.

## Scope

0.4.0 adds standard-format installation instructions and explicit Codex / Claude Code / generic host mappings. Rubric 1.1 and report schema 2.0 are unchanged from 0.3.0: mandatory grade, no independent audit, fresh scorer for every evaluation, separate HTML pages. No runtime host permission grants are embedded. Scripts are Python 3.10+ standard library only.

## Reproducible checks

```bash
python3 -m unittest discover -s skills/ai-capability-evaluator/tests -v
python3 skills/ai-capability-evaluator/scripts/report.py validate skills/ai-capability-evaluator/assets/example-report.json
python3 skills/ai-capability-evaluator/scripts/report.py render skills/ai-capability-evaluator/assets/example-report.json --output /tmp/ai-capability-evaluator-demo.html
```

The fixture is explicitly synthetic, not an actual model invocation. Trigger and output eval cases are authored fixtures, not a measured improvement over an unassisted model. Platform packaging and installer simulation are static checks, not Claude/Codex runtime acceptance. Detailed generated local gate logs are excluded from Git because they contain machine-specific paths.

Local release checks passed on 2026-11-10: 14 standard-library regression tests; 11 authored trigger cases; one file-backed output assertion case; Skill IR, validation/resource-budget checks; three-target compilation and static conformance; secret scan (zero findings); package verification and temporary install simulation for all three declared adapters. Upgrade metadata comparison reports a minor revision with no detected contract breaking changes. Drift inspection has no adoption data, not a positive usage result. Permission probes inspect metadata fallback rather than native filesystem enforcement. Review Studio is advisory and retains warnings for missing model/human calibration and operational evidence; no production promotion or independent sign-off is claimed.

Standard installer verification on 2026-11-10: `skills@1.7.6` discovered exactly one skill from the public GitHub repository. A real `npx --yes skills@1.7.6 add 1085995907ljh-hash/ai-capability-evaluator --skill ai-capability-evaluator --agent codex claude-code --yes` in a temporary project installed the shared Codex directory and Claude Code symlink, retained supporting files, created `skills-lock.json`, and appeared in `skills list --json`. Both installed paths successfully rendered the synthetic report. No existing global Skill installation was replaced. Installation tests disabled CLI telemetry. CI now tests installation from the checked-out source using the same pinned installer version. These are real installer tests, not model-driven candidate evaluation or a global-install runtime acceptance claim.

## Trust report

The two bundled scripts inventory explicit local paths and validate/render explicit report paths. They do not execute candidate code, make network requests or transmit candidates. HTML escapes untrusted text and includes no external assets. A hash fixes bytes, not authenticity. A fresh context does not provide filesystem isolation. Source originals remain read-only; candidate data stays outside this package. Actual writes and private-source access require a current task and host permission. No previous user's authorization is transferred to installers. `../security/permission_policy.json` records an automated source review of the local-write capability, explicitly not independent human approval or a runtime permission grant; its expiry is a maintainer recheck deadline.

## Evidence limits

missing evidence: human rubric calibration, blind human/model baseline, real Git/Office extraction coverage, cross-host model-driven end-to-end acceptance, browser clipboard execution and adoption telemetry. The public source and CI demonstrate structural tests; neither proves all formats or host contexts work automatically.

owner / review cadence / output contract / rollback boundary are in `../manifest.json`. `input_files` are synthetic file-backed fixtures in `../assets/` and `../evals/cases/`. See `output_quality_scorecard.md` for the scope of quality evidence.
