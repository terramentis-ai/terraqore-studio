# FlyntCore v1.1 Security Whitepaper (Phase 1)

## 1) Scope and Objectives
- Protect execution of AI-generated code against misuse, resource abuse, and hallucinated behaviors.
- Prevent prompt-injection and malicious payloads entering agent workflows.
- Provide auditable traces (transcripts, quotas, halt reasons) for executions and validations.

## 2) Threat Model (abridged)
- Adversary capabilities: crafted prompts, malicious code snippets, attempts to exfiltrate secrets, resource exhaustion, network egress, privilege escalation, dangerous shell commands.
- Surfaces: agent inputs (prompts/history), code generation outputs, code execution sandbox, API endpoints (task6_marketing), file operations.
- Assets: source tree, credentials/env vars, host resources (CPU/mem/fs), model/API keys, user data.

## 3) Mitigations Implemented
- Hallucination detection and halt
  - `HallucinationDetector`: AST syntax checks, undefined references, spec validation (required imports/functions/classes), suspicious pattern detection, unreachable-code checks, severity-weighted scoring with stricter penalties for critical/high.
  - `CodeValidationAgent`: halts on high/critical findings or low confidence; metadata includes severities, scores, and halt reason.
- Prompt-injection defense
  - `security_validator`: broadened pattern set (instruction overrides, filesystem wipe, secrets/API keys, DB drop/purge, restart/kill/monitoring disable, privilege escalation) across prompt, conversation, and context fields with decorator guard for agents.
- Sandboxed execution
  - `code_executor`: SandboxSpecification-driven quotas (CPU/memory/time/network/tmpfs/cap-drop/read-only root), optional Docker wrapping, POSIX soft limits, dangerous-output detection/halt, transcript logging (command, env, quotas applied, halt reason).
- Logging and auditability
  - Execution transcripts include timestamps, command line, working directory, quotas, dangerous pattern matches, exit codes; optional JSONL logging for post-mortem review.
- Test coverage
  - Security suite: hallucination detector (syntax, undefined refs, spec, security patterns, scoring, consistency), prompt injection patterns, sandbox executor dangerous-output halt and docker command assembly.

## 4) Validation Evidence (current)
- Tests: 46 passed, 3 skipped (benchmark-optional) via `python -m pytest core_cli/tests/security -q`.
- Executor: dangerous output halt verified; transcript quotas present; docker args assembled from presets (non-executing test path).
- Detector: required-import AST check prevents comment false positives; scoring now reflects critical findings; unreachable-code detection within indent scope.
- Validator: widened regexes cover API key/secret variants, backups, restart/kill/monitoring, privilege elevation.

## 5) Residual Risks and Limitations
- Docker enforcement optional: if docker unavailable or disabled, relies on POSIX soft limits + timeouts; no cgroup isolation in that mode.
- Network controls are best-effort; if docker not used, OS-level egress still possible via user environment.
- Dangerous-output detection is pattern-based; highly obfuscated payloads may evade patterns.
- No runtime syscall filtering beyond caps/seccomp defaults; high-assurance contexts may require stricter seccomp profiles and allowlist exec.
- Prompt-injection defense uses regex heuristics; extreme paraphrases may evade detection; needs periodic corpus refresh.

## 6) Recommendations for v1.1 Rollout
- Default to docker-backed execution in production; fail closed if docker unavailable for risky tasks.
- Enforce read-only root and cap-drop set from SandboxSpecification; disable network by default for code runs.
- Maintain JSONL execution logs with rotation and secure storage; ship to SIEM for anomaly detection.
- Add periodic red-team prompts to expand injection pattern set; retrain/refresh quarterly.
- Extend tests to cover API routes (task6_marketing) and file-ops guardrails; add contract tests for sandbox config parsing.
- Consider integrating secret scanners on stdout/stderr to catch exfil attempts; add egress firewall rules where possible.
