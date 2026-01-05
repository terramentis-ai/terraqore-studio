# MetaQore TODO (Updated January 4, 2026)

## Snapshot
- Phase: 2, Week 7 kickoff (governance endpoints + compliance exports)
- Environments: FastAPI unit suite green, mock LLM harness refreshed
- Repos: `metaqore/` only (push via `git subtree` to `terramentis` remote)

## ✅ Recently Completed
- Mock LLM client hardened with adversarial scenarios, edge-case generator, latency override, deterministic seeding, metadata hooks, and `StatefulConversationHandler` (`metaqore/mock_llm/client.py`, `__init__.py`).
- Copilot instructions updated with workspace boundaries + new status (`metaqore/.github/copilot-instructions.md`).
- Governance API surface landed: `/api/v1/governance/blocking-report`, `/api/v1/governance/compliance/export`, new schemas, router wiring, and unit coverage (`metaqore/api/routes/governance.py`, `tests/unit/test_api_governance.py`).

## 🚧 In Progress
1. Governance endpoints (Week 7)
   - [x] Expose PSMP blocking reports via `/api/v1/governance/blocking-report`.
   - [x] Expose compliance export endpoint delivering audit snapshots (CSV/JSON switch).
   - [x] Wire new routes into `metaqore/api/app.py` + dependency stack.
   - [x] Extend schemas/tests to cover new responses.
2. Documentation catch-up
   - [x] Document mock LLM scenarios + handler usage in `DEVELOPMENT_GUIDE.md` and `API_REFERENCE.md`.

## 🔜 Upcoming
- Add streaming/websocket hooks for governance notifications (Week 8 prep).
- Extend metrics/observability emitters to include mock LLM metadata fields.
- Run full unit suite once new endpoints land (`pytest tests/unit`).

## Notes
- Keep commits scoped to `metaqore/**` when syncing with the MetaQore repo.
- Prefer adding/adjusting tests alongside each new endpoint to keep the coverage story intact.
