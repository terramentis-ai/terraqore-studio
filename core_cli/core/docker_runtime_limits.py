"""
Docker Runtime Limits Specification and Implementation.

This module defines the security sandbox specifications for code execution
with Docker-backed runtime resource quotas and constraints.

Purpose:
- Define CPU/memory/time quota system for safe code execution
- Enforce strict resource limits to prevent resource exhaustion DoS
- Provide execution transcript logging and audit trails
- Enable rollback and dangerous output halt mechanisms

Author: DevOps Lead + Security Lead
Timeline: 2-3 days
Status: Foundation specification
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExecutionEnvironment(Enum):
    """Execution environment modes."""
    LOCAL = "local"           # Local subprocess execution
    DOCKER = "docker"         # Docker container execution
    KUBERNETES = "kubernetes" # Kubernetes pod execution


class ResourceQuotaLevel(Enum):
    """Predefined resource quota levels for different workload types."""
    MINIMAL = "minimal"       # Lightweight operations
    STANDARD = "standard"     # Normal code execution
    INTENSIVE = "intensive"   # Heavy computation
    UNRESTRICTED = "unrestricted"  # Admin/trusted operations


@dataclass
class CPUQuota:
    """CPU resource quota configuration."""
    
    # CPU configuration
    max_percentage: float = 80.0  # Maximum 80% of a single core
    cpus: float = 1.0            # Number of CPUs allocated (0.5-4.0)
    cpu_shares: int = 1024        # Docker CPU shares (1-1024)
    
    # Soft limits (process-level)
    cpu_time_seconds: Optional[int] = 30  # Max CPU seconds (RLIMIT_CPU)
    
    def to_docker_args(self) -> List[str]:
        """Convert to Docker run arguments."""
        args = []
        args.append(f"--cpus={self.cpus}")
        args.append(f"--cpu-shares={self.cpu_shares}")
        return args
    
    def validate(self) -> bool:
        """Validate configuration."""
        return (
            0 < self.max_percentage <= 100 and
            0.5 <= self.cpus <= 4.0 and
            1 <= self.cpu_shares <= 1024
        )


@dataclass
class MemoryQuota:
    """Memory resource quota configuration."""
    
    # Hard limits (container level)
    max_memory_mb: int = 2048          # Maximum memory: 2GB
    max_memory_swap_mb: Optional[int] = 2048  # Maximum swap
    
    # Soft limits (process level)
    memory_reservation_mb: int = 1024  # Reserved memory: 1GB
    
    # Out-of-memory policy
    oom_kill_disable: bool = False     # Kill container on OOM
    oom_score_adj: int = 0             # OOM killer priority (-1000 to 1000)
    
    def to_docker_args(self) -> List[str]:
        """Convert to Docker run arguments."""
        args = []
        args.append(f"--memory={self.max_memory_mb}m")
        if self.max_memory_swap_mb:
            args.append(f"--memory-swap={self.max_memory_swap_mb}m")
        args.append(f"--memory-reservation={self.memory_reservation_mb}m")
        if not self.oom_kill_disable:
            args.append("--oom-kill-disable=false")
        return args
    
    def validate(self) -> bool:
        """Validate configuration."""
        return (
            256 <= self.max_memory_mb <= 8192 and
            self.memory_reservation_mb <= self.max_memory_mb
        )


@dataclass
class TimeoutQuota:
    """Execution timeout configuration."""
    
    # Wall clock limits
    execution_timeout_seconds: int = 30     # Max execution time
    soft_timeout_seconds: Optional[int] = 25  # Graceful shutdown attempt
    
    # Initialization timeout
    startup_timeout_seconds: int = 10       # Time to start process
    
    def validate(self) -> bool:
        """Validate configuration."""
        return (
            1 <= self.execution_timeout_seconds <= 3600 and
            (self.soft_timeout_seconds is None or
             1 <= self.soft_timeout_seconds < self.execution_timeout_seconds)
        )


@dataclass
class NetworkQuota:
    """Network resource quota configuration."""
    
    # Network access
    enable_network: bool = False           # Enable network access
    network_mode: str = "none"            # Docker network mode
    
    # Bandwidth limits
    network_ingress_bytes_per_sec: Optional[int] = None
    network_egress_bytes_per_sec: Optional[int] = None
    
    def to_docker_args(self) -> List[str]:
        """Convert to Docker run arguments."""
        args = []
        args.append(f"--network={self.network_mode}")
        return args


@dataclass
class FilesystemQuota:
    """Filesystem resource quota configuration."""
    
    # Storage limits
    max_storage_mb: int = 1024         # Max output storage: 1GB
    max_file_size_mb: int = 100        # Max single file size
    max_file_count: int = 1000         # Max number of files
    
    # Temporary storage
    tmpfs_size_mb: int = 512           # Tmpfs/ramdisk size
    
    def to_docker_args(self) -> List[str]:
        """Convert to Docker run arguments."""
        args = []
        args.append(f"--tmpfs=/tmp:size={self.tmpfs_size_mb}m")
        return args


@dataclass
class SecurityQuota:
    """Security-related quota configuration."""
    
    # Capabilities
    cap_drop: List[str] = field(default_factory=lambda: [
        "NET_RAW",
        "NET_ADMIN",
        "SYS_ADMIN",
        "SYS_PTRACE",
        "SYS_BOOT",
        "MAC_ADMIN",
        "MAC_OVERRIDE",
    ])
    
    # Privilege mode
    privileged: bool = False
    read_only_root: bool = True
    
    # Seccomp/AppArmor
    security_opt: List[str] = field(default_factory=lambda: [
        "no-new-privileges:true"
    ])
    
    def to_docker_args(self) -> List[str]:
        """Convert to Docker run arguments."""
        args = []
        for cap in self.cap_drop:
            args.append(f"--cap-drop={cap}")
        if self.privileged:
            args.append("--privileged")
        if self.read_only_root:
            args.append("--read-only")
        for opt in self.security_opt:
            args.append(f"--security-opt={opt}")
        return args


@dataclass
class ExecutionTranscript:
    """Complete transcript of code execution for audit/debugging."""
    
    execution_id: str
    timestamp: datetime
    language: str
    file_path: str
    
    # Execution context
    environment_variables: Dict[str, str] = field(default_factory=dict)
    command_line: str = ""
    working_directory: str = ""
    
    # Resource usage
    cpu_time_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    wall_time_seconds: float = 0.0
    
    # Output
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    
    # Resource quotas applied
    quotas_applied: Dict[str, Any] = field(default_factory=dict)
    
    # Dangerous output detection
    dangerous_output_detected: bool = False
    dangerous_patterns: List[str] = field(default_factory=list)
    halt_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "language": self.language,
            "file_path": self.file_path,
            "environment_variables": {
                k: v for k, v in self.environment_variables.items()
                if not any(secret in k.upper() for secret in ["API", "KEY", "SECRET", "PASSWORD"])
            },
            "command_line": self.command_line,
            "working_directory": self.working_directory,
            "cpu_time_seconds": self.cpu_time_seconds,
            "memory_peak_mb": self.memory_peak_mb,
            "wall_time_seconds": self.wall_time_seconds,
            "stdout": self.stdout[:10000],  # Truncate for safety
            "stderr": self.stderr[:10000],
            "exit_code": self.exit_code,
            "quotas_applied": self.quotas_applied,
            "dangerous_output_detected": self.dangerous_output_detected,
            "dangerous_patterns": self.dangerous_patterns,
            "halt_reason": self.halt_reason,
        }


@dataclass
class RollbackMetadata:
    """Metadata for potential rollback operations."""
    
    execution_id: str
    rollback_reason: str
    timestamp: datetime
    
    # Files modified
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    
    # Database changes
    database_mutations: List[str] = field(default_factory=list)
    
    # Network activity
    network_connections: List[str] = field(default_factory=list)
    
    # State snapshots
    pre_execution_state: Dict[str, Any] = field(default_factory=dict)
    post_execution_state: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "rollback_reason": self.rollback_reason,
            "timestamp": self.timestamp.isoformat(),
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "database_mutations": self.database_mutations,
            "network_connections": self.network_connections,
        }


class SandboxSpecification:
    """
    Complete sandbox specification for Docker-backed code execution.
    
    Defines all resource quotas, security settings, and audit/logging
    requirements for safe code execution.
    """
    
    def __init__(
        self,
        level: ResourceQuotaLevel = ResourceQuotaLevel.STANDARD,
        cpu: Optional[CPUQuota] = None,
        memory: Optional[MemoryQuota] = None,
        timeout: Optional[TimeoutQuota] = None,
        network: Optional[NetworkQuota] = None,
        filesystem: Optional[FilesystemQuota] = None,
        security: Optional[SecurityQuota] = None,
    ):
        """Initialize sandbox specification."""
        self.level = level
        
        # Set defaults based on level
        if level == ResourceQuotaLevel.MINIMAL:
            self.cpu = cpu or CPUQuota(cpus=0.5, max_percentage=50)
            self.memory = memory or MemoryQuota(max_memory_mb=512, memory_reservation_mb=256)
            self.timeout = timeout or TimeoutQuota(execution_timeout_seconds=10)
        elif level == ResourceQuotaLevel.INTENSIVE:
            self.cpu = cpu or CPUQuota(cpus=4.0, max_percentage=100)
            self.memory = memory or MemoryQuota(max_memory_mb=8192, memory_reservation_mb=4096)
            self.timeout = timeout or TimeoutQuota(execution_timeout_seconds=300)
        else:  # STANDARD
            self.cpu = cpu or CPUQuota(cpus=1.0, max_percentage=80)
            self.memory = memory or MemoryQuota(max_memory_mb=2048, memory_reservation_mb=1024)
            self.timeout = timeout or TimeoutQuota(execution_timeout_seconds=30)
        
        self.network = network or NetworkQuota()
        self.filesystem = filesystem or FilesystemQuota()
        self.security = security or SecurityQuota()
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate all quota configurations.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not self.cpu.validate():
            errors.append("Invalid CPU quota configuration")
        if not self.memory.validate():
            errors.append("Invalid memory quota configuration")
        if not self.timeout.validate():
            errors.append("Invalid timeout quota configuration")
        
        return len(errors) == 0, errors
    
    def to_docker_run_args(self) -> List[str]:
        """Generate Docker run arguments for this specification."""
        args = []
        args.extend(self.cpu.to_docker_args())
        args.extend(self.memory.to_docker_args())
        args.extend(self.network.to_docker_args())
        args.extend(self.filesystem.to_docker_args())
        args.extend(self.security.to_docker_args())
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "level": self.level.value,
            "cpu": {
                "max_percentage": self.cpu.max_percentage,
                "cpus": self.cpu.cpus,
                "cpu_seconds": self.cpu.cpu_time_seconds,
            },
            "memory": {
                "max_memory_mb": self.memory.max_memory_mb,
                "memory_reservation_mb": self.memory.memory_reservation_mb,
            },
            "timeout": {
                "execution_timeout_seconds": self.timeout.execution_timeout_seconds,
                "soft_timeout_seconds": self.timeout.soft_timeout_seconds,
                "startup_timeout_seconds": self.timeout.startup_timeout_seconds,
            },
            "network": {
                "enable_network": self.network.enable_network,
                "network_mode": self.network.network_mode,
            },
            "filesystem": {
                "max_storage_mb": self.filesystem.max_storage_mb,
                "max_file_count": self.filesystem.max_file_count,
                "tmpfs_size_mb": self.filesystem.tmpfs_size_mb,
            },
        }


# Preset configurations for common use cases
PRESET_CONFIGURATIONS = {
    "test_execution": SandboxSpecification(ResourceQuotaLevel.MINIMAL),
    "standard_coding": SandboxSpecification(ResourceQuotaLevel.STANDARD),
    "data_processing": SandboxSpecification(ResourceQuotaLevel.INTENSIVE),
    "trusted_code": SandboxSpecification(
        ResourceQuotaLevel.STANDARD,
        cpu=CPUQuota(cpus=2.0, max_percentage=100),
        memory=MemoryQuota(max_memory_mb=4096),
        timeout=TimeoutQuota(execution_timeout_seconds=300),
    ),
}


def get_preset_configuration(preset_name: str) -> Optional[SandboxSpecification]:
    """Get a preset sandbox configuration.
    
    Args:
        preset_name: Name of the preset (test_execution, standard_coding, etc.)
        
    Returns:
        SandboxSpecification or None if preset not found
    """
    return PRESET_CONFIGURATIONS.get(preset_name)


if __name__ == "__main__":
    # Example usage and validation
    spec = SandboxSpecification(ResourceQuotaLevel.STANDARD)
    is_valid, errors = spec.validate()
    
    print(f"Specification valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    print("\nDocker run arguments:")
    for arg in spec.to_docker_run_args():
        print(f"  {arg}")
    
    print("\nConfiguration:")
    import json
    print(json.dumps(spec.to_dict(), indent=2))
