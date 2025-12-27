# FlyntCore v1.1 Security Rollout Checklist

## Pre-Deployment Verification
- [ ] Security tests passing: `python -m pytest core_cli/tests/security -q` (46 passed minimum)
- [ ] Docker installed and images pulled: `python:3.11-slim`, `node:18-alpine`
- [ ] Execution log directory configured with secure permissions
- [ ] Backup current production deployment

## Configuration Review
- [ ] Set `use_docker=true` for CodeExecutor in production environments
- [ ] Verify SandboxSpecification preset: `standard_coding` (or adjust per workload)
- [ ] Confirm network disabled by default: `network_mode="none"`
- [ ] Set execution log path with rotation policy

## Deployment
- [ ] Backend: activate venv, restart FastAPI service
- [ ] Verify CodeValidationAgent halt thresholds: `min_score=0.70`, `halt_severities={"high", "critical"}`
- [ ] Confirm security_validator loaded with expanded prompt-injection patterns
- [ ] Test docker_runtime_limits module imports successfully

## Post-Deployment Smoke Tests
- [ ] Run security test suite on target environment
- [ ] Execute safe sample: verify transcript created with quotas_applied
- [ ] Execute dangerous sample (rm -rf): confirm halt + dangerous_output_detected=true
- [ ] Trigger prompt injection: verify SecurityViolation raised
- [ ] Check JSONL logs written to configured path

## Monitoring Setup
- [ ] Forward executor logs to SIEM/logging platform
- [ ] Alert on: `dangerous_output_detected=true`, `halt_reason` present, non-zero exit codes
- [ ] Dashboard for SecurityViolation rate (prompt-injection attempts)
- [ ] Track docker execution failures if use_docker=true

## Rollback Preparedness
- [ ] Document previous stable tag/commit
- [ ] Preserve execution logs for forensics
- [ ] Test rollback procedure in staging

## Documentation Review
- [ ] SECURITY_WHITEPAPER_V1_1.md reviewed by security lead
- [ ] ROLLOUT_NOTES_V1_1.md reviewed by ops team
- [ ] Update MASTER_INDEX.md with security artifacts

## Known Gaps (defer to v1.2)
- [ ] API-level security tests for task6_marketing endpoints
- [ ] Secret scanner integration on stdout/stderr
- [ ] Outbound firewall rules for non-docker execution mode
- [ ] Seccomp allowlist profiles for high-assurance environments
- [ ] Prompt-injection corpus refresh (quarterly cadence)
