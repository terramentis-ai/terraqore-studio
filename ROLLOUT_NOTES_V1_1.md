# FlyntCore v1.1 Rollout Notes (Security Focus)

## Readiness Snapshot
- Security tests: 46 passed, 3 skipped (benchmark-optional) via `python -m pytest core_cli/tests/security -q`.
- New controls: hallucination halt (CodeValidationAgent), expanded prompt-injection regex set, sandbox executor with docker-aware quotas and dangerous-output halt, transcript logging.
- Risk posture: improved but docker enforcement remains optional; enable in production environments.

## Deployment Steps
1) Pre-flight
   - Ensure docker available on execution hosts; pull images: `python:3.11-slim`, `node:18-alpine` (or configured map).
   - Set default SandboxSpecification preset to `standard_coding`; disable network unless explicitly required.
   - Configure executor log path (JSONL) with rotation and secure permissions.
2) Deploy backend
   - Activate venv and apply migrations if any (none for security layer); restart FastAPI service.
   - Verify `code_executor` use_docker flag set for production workflows.
3) Frontend/UI
   - No security-specific UI changes required; ensure build uses latest code.
4) Post-deploy smoke
   - Run `python -m pytest core_cli/tests/security -q` on target environment.
   - Execute a sample safe script and a known dangerous payload to confirm halt + transcript logging.

## Monitoring and Observability
- Collect executor JSONL logs; forward to SIEM; alert on `dangerous_output_detected=true` or non-zero exit with halt_reason.
- Track rate of prompt-injection rejections (SecurityViolation); spike may indicate probing.
- Monitor docker failures (if use_docker=true); fail closed for untrusted tasks.

## Rollback Plan
- If sandbox/docker issues arise, toggle use_docker=false as temporary mitigation but restrict to non-sensitive workloads; re-enable after fix.
- Preserve execution logs for forensics; revert to previous stable tag if regressions persist.

## Known Gaps / Next Actions
- Add API-level security tests for task6_marketing endpoints and file-ops guardrails.
- Consider integrating secret scanners on stdout/stderr and outbound firewall rules for non-docker runs.
- Expand prompt-injection corpus quarterly; add obfuscation-resistant patterns.
- Add seccomp profile/allowlist for docker containers in high-assurance environments.
