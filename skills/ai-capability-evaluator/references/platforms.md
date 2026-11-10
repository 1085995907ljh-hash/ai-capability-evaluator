# Host adapters

The canonical artifact is a standard Agent Skill directory. `agents/openai.yaml` is optional Codex interface metadata. `agents/interface.yaml` and the manifest describe portability; they do not install tools or enforce permissions. Other hosts may ignore these metadata files and follow `SKILL.md`.

## Codex

Install in `~/.agents/skills/ai-capability-evaluator` or a project `.agents/skills/ai-capability-evaluator`. Older/configured hosts may use `~/.codex/skills`; follow the actual host configuration and avoid duplicate names. Resolve supporting paths from the installed skill root, not cwd.

If the host exposes `spawn_agent` with `fork_turns`, use `fork_turns="none"`. Supply the complete allowlisted scorer prompt; do not inherit the parent conversation. If that API is absent, use the host's equivalent new-context facility or a new ephemeral process with no resume. Never copy a platform-specific API name into an unavailable tool call.

When available, open the generated absolute HTML path with `open_in_codex` using file target and right placement. A queued/open request is not proof the user saw it; return the file link. Otherwise return an absolute file path or the host's supported preview link.

## Claude Code

Install in `~/.claude/skills/ai-capability-evaluator` or `.claude/skills/ai-capability-evaluator`. Invoke `/ai-capability-evaluator` or ask Claude to use it.

Delegate scoring to a NEW ordinary subagent using the host's Agent/Task tool. Send only the scoring role, rubric, output contract, grade-free packet and permitted excerpts/originals. Do not resume an old agent or use a fork inheriting conversation history. An existing agent's result or ID must not be reused for another score.

Disable persistent candidate memory. Host configuration, project instruction files and loaded rules can add context even when conversation history is fresh. On versions supporting `omitClaudeMd`, a custom scorer may use it to reduce unrelated project instructions; availability must be checked first. Regardless of version, ensure scorer input contains no candidate memories, previous scores or other candidates. If that cannot be ensured, use a genuinely clean ephemeral process or report the technical blockage. Never silently disable host security controls.

Return the generated HTML file path or use an available preview tool. A Codex right panel is not required.

## Generic hosts

Load `SKILL.md` and its relative references. Required capabilities: inspect actual source formats, launch a fresh scoring context without inherited candidate history, write UTF-8 JSON/HTML, and run Python 3.10+ for deterministic validation/rendering. Inventory uses POSIX file protection (macOS/Linux; Windows via WSL). No grading-model vendor is required. Do not change model or permission settings without authorization.

Without image/PDF/Office tools, mark affected sources unread and disclose the limitation. Without a fresh scoring context, preserve intake and report a tool blockage rather than presenting a fabricated fresh score. Without a preview panel, deliver HTML paths/links. Standard-format compatibility alone does not prove a host completed an end-to-end evaluation.

## References and verification boundary

- Agent Skills format: https://agentskills.io/specification
- Codex skill locations: https://learn.chatgpt.com/docs/build-skills
- Claude skill locations: https://code.claude.com/docs/en/skills
- Claude subagent context: https://code.claude.com/docs/en/sub-agents

These references inform the adapters. Static compatibility/package checks are distinct from actual model invocation and real-document extraction; see `../reports/verification.md`.
