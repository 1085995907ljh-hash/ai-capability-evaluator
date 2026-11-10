# Output contract 2.0

UTF-8 JSON. Runtime candidate inputs remain outside the skill. `assets/example-report.json` is a synthetic file-backed fixture, never a real candidate.

Required report fields:
```
schema_version: "2.0"
rubric_version: "1.1"
demo: boolean
candidate: {id: string, name: string}
materials: [{id, label, format, coverage, limitations: [string]}]
evidence: [{id, material_id, locator, observation,
           kind: "artifact"|"self_report"|"inference",
           supports: [string], limits: [string]}]
understanding: {work_summary, contribution, limitations: [string]}
assessment: {
 proposed_level: "Assisted"|"L1"|"L2"|"L3"|"L4",
 rating_status: "supported"|"provisional",
 confidence: "high"|"medium"|"low",
 evidence_gaps: [string],
 reason: string (160–260 non-whitespace characters),
 material_reviews: [{material_id, summary, interpretation, limitation,
                     evidence_ids: [string]}],
 level_explanation: string,
 higher_level_explanation: string,
 level_basis: [{criterion, finding, evidence_ids: [string]}]
}
evaluation: {
 scorer_id: actual host invocation ID,
 scorer_fresh: true,
 context_mode: string,
 packet_version: string
}
```
Listed scalar fields are strings unless specified. No null grade, audit, rounds or dimension fields. supported means material-supported, not external verification. provisional is only the Assisted floor with confidence=low and nonempty evidence_gaps. Explicitly disclose provisional status in both reason and level_explanation.

IDs are opaque and unique. All evidence references resolve. Each material gets one material_review citing only that material's evidence; array order matches input order. supported requires nonempty level_basis with evidence for each chosen condition. Provisional floor may have empty level_basis. Missing evidence can remain evidence_gaps for any level; it never becomes fabricated facts. The scorer assesses semantic support; deterministic validation cannot authenticate evidence or judge fairness.

Keep source manifests and actual scorer invocation receipts (context mode, input/output hashes) outside the skill. No auditor is required or launched. No fabricated IDs/fresh flags.

## HTML and navigation

Each person MUST have a separate directory with report.json and report.html. Exactly two main sections:
1. 总结: copyable text with only 候选人、等级、理由 (~200 characters). Put provisional disclosure in the reason, so copied text cannot hide it. Display a material-based/provisional badge outside copied text.
2. 具体评判过程: short per-file paragraphs describing contents, support and limits, with concise text-only locators; then why this level and why the next higher level is unsupported.

No visible dimension tables, evidence ledger, interview questions, audit results, approval badges or review rounds. Footer states grading uses current materials and has no independent audit; do not claim verified competence. Demo is visibly labeled including copied name.

Offline, UTF-8, responsive, printable; escaped candidate text, no remote assets, raw source HTML, secret paths or analytics. Clipboard fallback must work without navigator.clipboard.

Render: `report.py render <run>/report.json --output <run>/report.html`.
Browse: `report.py index <run1>/report.json <run2>/report.json --output <batch>/index.html`.
Index validates each report, requires an existing sibling report.html matching its current JSON bytes, and links using relative local paths. No rankings or invented placeholders. Update after each person; opening a link shows that person's distinct page. Never overwrite input JSON or another report via index output.

## Migration

0.3.0 replaces 0.2.0 schema 1.1/rubric 1.0. Retain old evaluations as historical. Use a NEW scorer on a grade-free packet with rubric 1.1; do not copy old null/grades/reasons or audit feedback. New JSON has no audit/rounds. Missing error cases are limits, not a veto; L2's own error-detection condition stays intact.
