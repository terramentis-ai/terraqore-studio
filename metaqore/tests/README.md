# Tests

## Structure
- Unit tests live under `tests/unit/`.
- Integration/system specs live under `tests/integration/` to avoid pytest module name collisions with unit files.

## Commands
- Run full suite: `pytest`
- Target governance: `pytest tests/unit/test_api_governance.py -v`

## Naming
- Use `test_*_integration.py` for integration specs placed in `tests/integration/`.
- Avoid reusing unit test module names to prevent import collisions.
