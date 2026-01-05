"""Validation gate runner scaffold derived from hmcp.json."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping

from metaqore.core.models import SpecialistModel

from .training import TrainingOutcome


@dataclass(frozen=True)
class ValidationStageResult:
    """Result for a single validation gate stage."""

    stage: str
    passed: bool
    details: Dict[str, Any]


@dataclass(frozen=True)
class ValidationGateReport:
    """Aggregate report representing the entire validation suite."""

    passed: bool
    stages: List[ValidationStageResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "stages": [stage.__dict__ for stage in self.stages],
        }


class ValidationGateRunner:
    """Executes the configured validation stages over a specialist."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        stages = list(config.get("stages", []))
        if not stages:
            raise ValueError("validation_gate config must define at least one stage")
        self._stages = stages

    def run(self, specialist: SpecialistModel, outcome: TrainingOutcome) -> ValidationGateReport:
        stage_results: List[ValidationStageResult] = []
        for stage in self._stages:
            stage_name = stage.get("stage", "unknown_stage")
            result = self._run_stage(stage_name, stage, specialist, outcome)
            stage_results.append(result)
        passed = all(stage.passed for stage in stage_results)
        return ValidationGateReport(passed=passed, stages=stage_results)

    def _run_stage(
        self,
        stage_name: str,
        stage_config: Mapping[str, Any],
        specialist: SpecialistModel,
        outcome: TrainingOutcome,
    ) -> ValidationStageResult:
        details: Dict[str, Any] = {}
        passed = True
        metrics = outcome.metrics

        if stage_name == "functional_unit_test":
            threshold = float(stage_config.get("passing_score", 0.95))
            score = metrics.get("functional_accuracy", specialist.confidence)
            passed = score >= threshold
            details = {"score": score, "threshold": threshold}
        elif stage_name == "catastrophic_forgetting_test":
            allowed_drop = float(stage_config.get("max_performance_drop", 0.01))
            previous = specialist.metadata.get("teacher_baseline", 0.95)
            score = metrics.get("functional_accuracy", specialist.confidence)
            drop = max(0.0, previous - score)
            passed = drop <= allowed_drop
            details = {"baseline": previous, "score": score, "drop": drop, "max_drop": allowed_drop}
        elif stage_name == "adversarial_robustness":
            required = bool(stage_config.get("must_pass", True))
            robustness = metrics.get("robustness", metrics.get("robustness_score", 0.9))
            passed = robustness >= 0.9 if required else True
            details = {"robustness": robustness, "required": required}
        elif stage_name == "psmp_compatibility_check":
            must_pass = bool(stage_config.get("must_pass", True))
            conflict_count = len(specialist.blocked_by)
            passed = conflict_count == 0 if must_pass else True
            details = {"conflicts": conflict_count, "must_pass": must_pass}
        else:
            details = {"reason": "stage_not_implemented"}

        return ValidationStageResult(stage=stage_name, passed=passed, details=details)


__all__ = ["ValidationGateReport", "ValidationGateRunner", "ValidationStageResult"]
