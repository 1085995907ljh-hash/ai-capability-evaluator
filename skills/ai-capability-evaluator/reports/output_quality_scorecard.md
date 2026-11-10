# Output quality scorecard

Release: 0.4.0. output contract: schema 2.0. input_files: synthetic file-backed fixture.

| Check | Evidence | Limit |
| --- | --- | --- |
| Report schema and compulsory grade | Regression tests + synthetic JSON validation | Does not establish whether a grade is factually correct |
| Disclosure of provisional Assisted | Tests reject hidden uncertainty / inflated provisional level | Human interpretation remains unmeasured |
| Per-file evidence association | Tests for ownership, ordering and locator references | Source authenticity is not verified |
| One page per person and linked index | Distinct HTML rendering / stale-output regression tests | Clipboard and visual browser acceptance are missing evidence |
| Prompt injection in display strings | HTML escaping regression tests | Does not prove model resistance to every injected source |
| Trigger and output assertions | Authored positive, negative and contrast fixtures | No model routing benchmark or blind human baseline |
| Cross-host compatibility | Neutral Skill source and platform mappings | Actual Claude / generic model-driven workflow is missing evidence |

No independent candidate audit is part of this workflow. Maintainer checks are software release checks, not an audit of candidates or human sign-off. Owner: repository maintainer. Review cadence: every release. Rollback boundary: restore prior Skill files; preserve candidate run history independently.
