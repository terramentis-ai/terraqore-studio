"""
TerraQore Secure Gateway - Phase 5 Security-First Routing

Extends LLM Gateway with task-based security classification and policy enforcement.
Ensures sensitive tasks stay local, respects organization policies, and maintains audit trail.
"""

import logging
import asyncio
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskSensitivity(Enum):
    """Classification levels for task sensitivity."""
    PUBLIC = "public"               # Task can use cloud (cost optimization OK)
    INTERNAL = "internal"           # Prefer local, cloud allowed with user consent
    SENSITIVE = "sensitive"         # Must use local if available, error if unavailable
    CRITICAL = "critical"           # Never cloud, error if local unavailable


class RoutingPolicy(ABC):
    """Abstract base for organization-specific routing policies."""
    
    @abstractmethod
    def should_allow_cloud(self, task_sensitivity: TaskSensitivity) -> bool:
        """Determine if cloud is allowed for this sensitivity level."""
        pass
    
    @abstractmethod
    def get_allowed_providers(self, task_sensitivity: TaskSensitivity) -> List[str]:
        """Get list of allowed providers for this sensitivity level."""
        pass
    
    @abstractmethod
    def get_audit_context(self) -> Dict[str, Any]:
        """Get organization context for audit logging."""
        pass


class DefaultRoutingPolicy(RoutingPolicy):
    """Default policy: LOCAL-FIRST security model."""
    
    def should_allow_cloud(self, task_sensitivity: TaskSensitivity) -> bool:
        """
        Policy:
        - CRITICAL: Never cloud
        - SENSITIVE: Never cloud
        - INTERNAL: Cloud allowed (user preference)
        - PUBLIC: Cloud allowed
        """
        if task_sensitivity in [TaskSensitivity.CRITICAL, TaskSensitivity.SENSITIVE]:
            return False
        return True
    
    def get_allowed_providers(self, task_sensitivity: TaskSensitivity) -> List[str]:
        """
        Provider whitelist by sensitivity:
        - CRITICAL: [ollama] only
        - SENSITIVE: [ollama] only
        - INTERNAL: [ollama, openrouter] (user preference)
        - PUBLIC: [ollama, openrouter] (cost optimization)
        """
        if task_sensitivity in [TaskSensitivity.CRITICAL, TaskSensitivity.SENSITIVE]:
            return ["ollama"]
        return ["ollama", "openrouter"]
    
    def get_audit_context(self) -> Dict[str, Any]:
        return {
            "policy_name": "default_local_first",
            "description": "Local-first security model with cloud fallback for non-sensitive tasks"
        }


class EnterpriseRoutingPolicy(RoutingPolicy):
    """Enterprise policy: Data residency + compliance requirements."""
    
    def __init__(self, region: str = "local", requires_encryption: bool = True):
        self.region = region
        self.requires_encryption = requires_encryption
    
    def should_allow_cloud(self, task_sensitivity: TaskSensitivity) -> bool:
        """Enterprise policy: Only non-critical tasks can use cloud."""
        return task_sensitivity in [TaskSensitivity.PUBLIC, TaskSensitivity.INTERNAL]
    
    def get_allowed_providers(self, task_sensitivity: TaskSensitivity) -> List[str]:
        """Enterprise policy: Strict data residency."""
        if task_sensitivity in [TaskSensitivity.CRITICAL, TaskSensitivity.SENSITIVE]:
            return ["ollama"]  # Local only
        if task_sensitivity == TaskSensitivity.INTERNAL:
            return ["ollama"]  # Internal data stays local
        return ["ollama", "openrouter"]  # Only public data can go cloud
    
    def get_audit_context(self) -> Dict[str, Any]:
        return {
            "policy_name": "enterprise_data_residency",
            "region": self.region,
            "requires_encryption": self.requires_encryption,
            "description": f"Enterprise policy with {self.region} data residency requirement"
        }


class CompliancePolicy(RoutingPolicy):
    """HIPAA/GDPR/SOC2 compliance policy: Strictest security."""
    
    def __init__(self, framework: str = "GDPR"):
        self.framework = framework
    
    def should_allow_cloud(self, task_sensitivity: TaskSensitivity) -> bool:
        """Compliance policy: Never send any task data to cloud."""
        return False  # All tasks stay local
    
    def get_allowed_providers(self, task_sensitivity: TaskSensitivity) -> List[str]:
        """Compliance policy: Local only for all tasks."""
        return ["ollama"]
    
    def get_audit_context(self) -> Dict[str, Any]:
        return {
            "policy_name": f"compliance_{self.framework.lower()}",
            "framework": self.framework,
            "description": f"{self.framework} compliant - all processing local"
        }


@dataclass
class ComplianceAuditLog:
    """Audit log entry for compliance tracking."""
    timestamp: str
    agent_name: str
    task_type: str
    sensitivity: str
    selected_provider: str
    policy_decision: str  # Why this provider was chosen
    policy_name: str
    organization: str
    data_residency: str  # Where data was processed
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "agent_name": self.agent_name,
            "task_type": self.task_type,
            "sensitivity": self.sensitivity,
            "selected_provider": self.selected_provider,
            "policy_decision": self.policy_decision,
            "policy_name": self.policy_name,
            "organization": self.organization,
            "data_residency": self.data_residency,
            "metadata": self.metadata
        }


class ComplianceAuditor:
    """Maintains audit trail for compliance requirements."""
    
    def __init__(self, organization: str = "default", log_file: Optional[str] = None):
        self.organization = organization
        self.log_file = log_file or f"core_cli/logs/compliance_audit_{organization}.jsonl"
        self.logs: List[ComplianceAuditLog] = []
        self._load_existing_logs()

    def _load_existing_logs(self) -> None:
        """Load existing audit logs from disk so reports include history."""
        log_path = Path(self.log_file)
        if not log_path.exists():
            return
        try:
            with log_path.open('r') as f:
                for line in f:
                    data = line.strip()
                    if not data:
                        continue
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError as exc:
                        logger.warning(f"Skipping corrupted audit log line: {exc}")
                        continue
                    self.logs.append(
                        ComplianceAuditLog(
                            timestamp=payload.get("timestamp", ""),
                            agent_name=payload.get("agent_name", "unknown"),
                            task_type=payload.get("task_type", "unknown"),
                            sensitivity=payload.get("sensitivity", "unknown"),
                            selected_provider=payload.get("selected_provider", "unknown"),
                            policy_decision=payload.get("policy_decision", ""),
                            policy_name=payload.get("policy_name", "unknown"),
                            organization=payload.get("organization", self.organization),
                            data_residency=payload.get("data_residency", "unknown"),
                            metadata=payload.get("metadata") or {}
                        )
                    )
        except Exception as e:
            logger.error(f"Failed to load compliance logs: {e}")
    
    def log_routing_decision(
        self,
        agent_name: str,
        task_type: str,
        sensitivity: TaskSensitivity,
        selected_provider: str,
        policy_decision: str,
        policy_name: str,
        data_residency: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a routing decision for compliance tracking."""
        log_entry = ComplianceAuditLog(
            timestamp=datetime.utcnow().isoformat(),
            agent_name=agent_name,
            task_type=task_type,
            sensitivity=sensitivity.value,
            selected_provider=selected_provider,
            policy_decision=policy_decision,
            policy_name=policy_name,
            organization=self.organization,
            data_residency=data_residency,
            metadata=metadata or {}
        )
        
        self.logs.append(log_entry)
        self._write_to_file(log_entry)
        
        logger.info(
            f"[AUDIT] {agent_name}|{task_type}|{sensitivity.value}|{selected_provider}|{data_residency}"
        )
    
    def _write_to_file(self, log_entry: ComplianceAuditLog) -> None:
        """Append audit log to file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_logs(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve audit logs, optionally filtered by agent."""
        logs = self.logs
        if agent_name:
            logs = [log for log in logs if log.agent_name == agent_name]
        return [log.to_dict() for log in logs]
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report from audit logs."""
        report = {
            "organization": self.organization,
            "generated_at": datetime.utcnow().isoformat(),
            "total_tasks": len(self.logs),
            "local_tasks": len([log for log in self.logs if log.selected_provider == "ollama"]),
            "cloud_tasks": len([log for log in self.logs if log.selected_provider != "ollama"]),
            "critical_tasks": len([log for log in self.logs if log.sensitivity == "critical"]),
            "sensitive_tasks": len([log for log in self.logs if log.sensitivity == "sensitive"]),
            "by_agent": {},
            "by_sensitivity": {}
        }
        
        # Group by agent
        for log in self.logs:
            if log.agent_name not in report["by_agent"]:
                report["by_agent"][log.agent_name] = {"local": 0, "cloud": 0}
            if log.selected_provider == "ollama":
                report["by_agent"][log.agent_name]["local"] += 1
            else:
                report["by_agent"][log.agent_name]["cloud"] += 1
        
        # Group by sensitivity
        for sensitivity in TaskSensitivity:
            count = len([log for log in self.logs if log.sensitivity == sensitivity.value])
            if count > 0:
                report["by_sensitivity"][sensitivity.value] = count
        
        return report


class SecureGateway:
    """
    Security-first routing gateway for TerraQore.
    
    Extends LLM Gateway with task sensitivity classification and policy enforcement.
    Ensures sensitive tasks respect organization policies and maintains audit trail.
    """
    
    def __init__(
        self,
        policy: Optional[RoutingPolicy] = None,
        organization: str = "default",
        audit_enabled: bool = True
    ):
        """
        Initialize SecureGateway.
        
        Args:
            policy: Routing policy (defaults to DefaultRoutingPolicy)
            organization: Organization name for audit logs
            audit_enabled: Enable compliance audit logging
        """
        self.policy = policy or DefaultRoutingPolicy()
        self.organization = organization
        self.auditor = ComplianceAuditor(organization) if audit_enabled else None
        logger.info(f"SecureGateway initialized with {type(self.policy).__name__}")
    
    def classify_task(
        self,
        agent_name: str,
        task_type: str,
        has_private_data: bool = False,
        has_sensitive_data: bool = False,
        is_security_task: bool = False
    ) -> TaskSensitivity:
        """
        Classify task by sensitivity level based on characteristics.
        
        Args:
            agent_name: Name of agent performing task
            task_type: Type of task (e.g., 'code_generation', 'security_analysis')
            has_private_data: Contains private/internal data
            has_sensitive_data: Contains sensitive data (PII, credentials, etc.)
            is_security_task: Is security/compliance related
            
        Returns:
            TaskSensitivity classification
        """
        # Security tasks are always CRITICAL
        if is_security_task or agent_name == "SecurityVulnerabilityAgent":
            return TaskSensitivity.CRITICAL
        
        # Data processing with sensitive data
        if has_sensitive_data:
            return TaskSensitivity.CRITICAL
        
        # Internal data processing
        if has_private_data:
            return TaskSensitivity.SENSITIVE
        
        # Code review of private code
        if task_type == "code_review" and has_private_data:
            return TaskSensitivity.SENSITIVE
        
        # Default: internal tasks are INTERNAL, others PUBLIC
        if task_type in ["planning", "analysis", "validation", "documentation"]:
            return TaskSensitivity.INTERNAL
        
        return TaskSensitivity.PUBLIC
    
    def validate_provider_allowed(
        self,
        provider: str,
        sensitivity: TaskSensitivity,
        agent_name: str,
        task_type: str
    ) -> bool:
        """
        Validate if provider is allowed for this task sensitivity.
        
        Args:
            provider: Provider name ('ollama', 'openrouter', etc.)
            sensitivity: Task sensitivity level
            agent_name: Name of agent
            task_type: Type of task
            
        Returns:
            True if allowed, False otherwise
        """
        allowed_providers = self.policy.get_allowed_providers(sensitivity)
        
        if provider not in allowed_providers:
            logger.warning(
                f"Provider '{provider}' not allowed for {sensitivity.value} task "
                f"({agent_name}/{task_type}). Allowed: {allowed_providers}"
            )
            
            if self.auditor:
                self.auditor.log_routing_decision(
                    agent_name=agent_name,
                    task_type=task_type,
                    sensitivity=sensitivity,
                    selected_provider="BLOCKED",
                    policy_decision=f"Provider {provider} not allowed for {sensitivity.value} tasks",
                    policy_name=type(self.policy).__name__,
                    data_residency="local",
                    metadata={"blocked_provider": provider, "allowed": allowed_providers}
                )
            
            return False
        
        return True
    
    def get_recommended_provider(
        self,
        sensitivity: TaskSensitivity,
        local_available: bool = True,
        cloud_available: bool = True,
        agent_name: str = "unknown",
        task_type: str = "unknown"
    ) -> str:
        """
        Get recommended provider based on sensitivity and availability.
        
        Args:
            sensitivity: Task sensitivity level
            local_available: Is Ollama available
            cloud_available: Is cloud provider available
            agent_name: Name of agent
            task_type: Type of task
            
        Returns:
            Recommended provider name or raises exception if no valid provider
        """
        allowed_providers = self.policy.get_allowed_providers(sensitivity)
        
        # CRITICAL/SENSITIVE: must use local
        if sensitivity in [TaskSensitivity.CRITICAL, TaskSensitivity.SENSITIVE]:
            if "ollama" in allowed_providers and local_available:
                if self.auditor:
                    self.auditor.log_routing_decision(
                        agent_name=agent_name,
                        task_type=task_type,
                        sensitivity=sensitivity,
                        selected_provider="ollama",
                        policy_decision=f"{sensitivity.value} task - using local provider",
                        policy_name=type(self.policy).__name__,
                        data_residency="local"
                    )
                return "ollama"
            else:
                error_msg = f"No local provider available for {sensitivity.value} task"
                logger.error(f"[POLICY VIOLATION] {error_msg} - {agent_name}/{task_type}")
                
                if self.auditor:
                    self.auditor.log_routing_decision(
                        agent_name=agent_name,
                        task_type=task_type,
                        sensitivity=sensitivity,
                        selected_provider="FAILED",
                        policy_decision=error_msg,
                        policy_name=type(self.policy).__name__,
                        data_residency="local"
                    )
                
                raise RuntimeError(error_msg)
        
        # INTERNAL/PUBLIC: prefer local, allow cloud
        if "ollama" in allowed_providers and local_available:
            provider = "ollama"
            decision = "prefer_local"
        elif "openrouter" in allowed_providers and cloud_available:
            provider = "openrouter"
            decision = "fallback_cloud"
        else:
            error_msg = f"No available provider for {sensitivity.value} task"
            logger.error(f"[POLICY VIOLATION] {error_msg}")
            raise RuntimeError(error_msg)
        
        if self.auditor:
            self.auditor.log_routing_decision(
                agent_name=agent_name,
                task_type=task_type,
                sensitivity=sensitivity,
                selected_provider=provider,
                policy_decision=f"{sensitivity.value} task - {decision}",
                policy_name=type(self.policy).__name__,
                data_residency="local" if provider == "ollama" else "cloud"
            )
        
        return provider
    
    def get_audit_report(self) -> Dict[str, Any]:
        """Get compliance audit report."""
        if not self.auditor:
            return {"error": "Audit logging disabled"}
        return self.auditor.generate_compliance_report()
    
    def set_policy(self, policy: RoutingPolicy) -> None:
        """Change routing policy at runtime."""
        self.policy = policy
        logger.info(f"SecureGateway policy changed to {type(policy).__name__}")


# Convenience function to get secure gateway instance
_secure_gateway = None

def get_secure_gateway(
    policy: Optional[RoutingPolicy] = None,
    organization: str = "default",
    audit_enabled: bool = True
) -> SecureGateway:
    """Get or create SecureGateway instance."""
    global _secure_gateway
    if _secure_gateway is None:
        _secure_gateway = SecureGateway(policy, organization, audit_enabled)
    return _secure_gateway
