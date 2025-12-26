"""
Flynt Error Recovery System
Provides strategies for handling and recovering from agent/system failures.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types."""
    API_ERROR = "api_error"           # LLM API failures
    VALIDATION_ERROR = "validation_error"  # Output validation failures
    TIMEOUT_ERROR = "timeout_error"   # Operation timeouts
    RESOURCE_ERROR = "resource_error" # Out of resources
    DATABASE_ERROR = "database_error" # Database operation failures
    UNKNOWN_ERROR = "unknown_error"   # Uncategorized errors


class RecoverySeverity(Enum):
    """Severity of failure requiring recovery."""
    RECOVERABLE = "recoverable"       # Can automatically recover
    DEGRADED = "degraded"             # Partial recovery possible
    CRITICAL = "critical"             # Requires manual intervention


@dataclass
class ErrorContext:
    """Context information about an error."""
    error_type: ErrorType
    severity: RecoverySeverity
    message: str
    timestamp: datetime
    agent_name: Optional[str] = None
    task_id: Optional[int] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    message: str
    recovered_value: Optional[Any] = None
    recovery_time_ms: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ErrorRecoveryStrategy(ABC):
    """Abstract base class for error recovery strategies."""
    
    @abstractmethod
    def can_recover(self, error: ErrorContext) -> bool:
        """Check if this strategy can handle the given error.
        
        Args:
            error: Error context.
            
        Returns:
            True if strategy can attempt recovery.
        """
        pass
    
    @abstractmethod
    async def recover(self, error: ErrorContext) -> RecoveryResult:
        """Attempt to recover from the error.
        
        Args:
            error: Error context.
            
        Returns:
            RecoveryResult with outcome.
        """
        pass
    
    def _log_recovery_attempt(self, error: ErrorContext, strategy_name: str):
        """Log recovery attempt."""
        logger.info(
            f"Attempting {strategy_name} recovery for {error.error_type.value} "
            f"in agent '{error.agent_name}' (attempt {error.retry_count + 1})"
        )


class RetryStrategy(ErrorRecoveryStrategy):
    """Retry failed operations with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        """Initialize retry strategy.
        
        Args:
            max_retries: Maximum retry attempts.
            initial_delay: Initial delay in seconds.
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
    
    def can_recover(self, error: ErrorContext) -> bool:
        """Retry most transient errors but not validation or critical resource errors."""
        if error.retry_count >= self.max_retries:
            return False
        return error.error_type in [
            ErrorType.API_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.DATABASE_ERROR
        ]
    
    async def recover(self, error: ErrorContext) -> RecoveryResult:
        """Retry the operation with exponential backoff."""
        self._log_recovery_attempt(error, "Retry")
        
        start_time = time.time()
        backoff_delay = self.initial_delay * (2 ** error.retry_count)
        
        logger.info(f"Waiting {backoff_delay}s before retry...")
        time.sleep(backoff_delay)
        
        recovery_time_ms = (time.time() - start_time) * 1000
        return RecoveryResult(
            success=True,
            message=f"Retry scheduled after {backoff_delay}s backoff",
            recovery_time_ms=recovery_time_ms,
            metadata={"backoff_delay": backoff_delay, "retry_number": error.retry_count + 1}
        )


class FallbackStrategy(ErrorRecoveryStrategy):
    """Switch to alternative provider or method on failure."""
    
    def __init__(self, fallback_fn: Optional[Callable] = None):
        """Initialize fallback strategy.
        
        Args:
            fallback_fn: Optional callable to execute as fallback.
        """
        self.fallback_fn = fallback_fn
    
    def can_recover(self, error: ErrorContext) -> bool:
        """Can fallback to alternative provider."""
        return error.error_type in [
            ErrorType.API_ERROR,
            ErrorType.TIMEOUT_ERROR
        ] and error.severity != RecoverySeverity.CRITICAL
    
    async def recover(self, error: ErrorContext) -> RecoveryResult:
        """Execute fallback function if available."""
        self._log_recovery_attempt(error, "Fallback")
        
        start_time = time.time()
        
        if self.fallback_fn is None:
            return RecoveryResult(
                success=False,
                message="No fallback function configured",
                recovery_time_ms=(time.time() - start_time) * 1000
            )
        
        try:
            result = self.fallback_fn() if not hasattr(self.fallback_fn, '__await__') else await self.fallback_fn()
            recovery_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Fallback recovery succeeded in {recovery_time_ms:.0f}ms")
            return RecoveryResult(
                success=True,
                message="Fallback executed successfully",
                recovered_value=result,
                recovery_time_ms=recovery_time_ms
            )
        except Exception as e:
            recovery_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Fallback recovery failed: {str(e)}")
            return RecoveryResult(
                success=False,
                message=f"Fallback execution failed: {str(e)}",
                recovery_time_ms=recovery_time_ms
            )


class CircuitBreakerStrategy(ErrorRecoveryStrategy):
    """Implement circuit breaker pattern to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60.0):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit.
            reset_timeout: Seconds before attempting to reset circuit.
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def can_recover(self, error: ErrorContext) -> bool:
        """Can implement circuit breaker logic."""
        return error.error_type in [ErrorType.API_ERROR, ErrorType.TIMEOUT_ERROR]
    
    async def recover(self, error: ErrorContext) -> RecoveryResult:
        """Manage circuit breaker state."""
        self._log_recovery_attempt(error, "CircuitBreaker")
        
        start_time = time.time()
        
        # Check if we can attempt reset
        if self.is_open and self.last_failure_time:
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure > self.reset_timeout:
                logger.info("Circuit breaker timeout expired, attempting reset...")
                self.is_open = False
                self.failure_count = 0
                return RecoveryResult(
                    success=True,
                    message="Circuit breaker reset attempted",
                    recovery_time_ms=(time.time() - start_time) * 1000
                )
        
        # Update failure tracking
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                f"Circuit breaker OPEN after {self.failure_count} failures. "
                f"Blocking requests for {self.reset_timeout}s"
            )
            return RecoveryResult(
                success=False,
                message="Circuit breaker is OPEN - request rejected",
                recovery_time_ms=(time.time() - start_time) * 1000,
                metadata={"circuit_open": True, "failure_count": self.failure_count}
            )
        
        return RecoveryResult(
            success=True,
            message=f"Circuit breaker tracking failure ({self.failure_count}/{self.failure_threshold})",
            recovery_time_ms=(time.time() - start_time) * 1000,
            metadata={"failure_count": self.failure_count}
        )


class DeadLetterStrategy(ErrorRecoveryStrategy):
    """Store failed operations for later processing or analysis."""
    
    def __init__(self, max_queue_size: int = 1000):
        """Initialize dead letter queue.
        
        Args:
            max_queue_size: Maximum stored failed operations.
        """
        self.max_queue_size = max_queue_size
        self.dead_letters: list[Dict[str, Any]] = []
    
    def can_recover(self, error: ErrorContext) -> bool:
        """Can store for later processing."""
        return error.severity == RecoverySeverity.CRITICAL
    
    async def recover(self, error: ErrorContext) -> RecoveryResult:
        """Store error in dead letter queue."""
        self._log_recovery_attempt(error, "DeadLetter")
        
        start_time = time.time()
        
        if len(self.dead_letters) >= self.max_queue_size:
            logger.warning(f"Dead letter queue full ({self.max_queue_size} items)")
            return RecoveryResult(
                success=False,
                message="Dead letter queue is full",
                recovery_time_ms=(time.time() - start_time) * 1000
            )
        
        dead_letter = {
            "timestamp": error.timestamp.isoformat(),
            "error_type": error.error_type.value,
            "message": error.message,
            "agent_name": error.agent_name,
            "task_id": error.task_id,
            "metadata": error.metadata
        }
        
        self.dead_letters.append(dead_letter)
        logger.info(f"Stored dead letter ({len(self.dead_letters)}/{self.max_queue_size})")
        
        return RecoveryResult(
            success=True,
            message="Error stored in dead letter queue for analysis",
            recovery_time_ms=(time.time() - start_time) * 1000,
            metadata={"queue_size": len(self.dead_letters)}
        )
    
    def get_dead_letters(self) -> list[Dict[str, Any]]:
        """Retrieve all dead letters."""
        return self.dead_letters.copy()
    
    def clear_dead_letters(self):
        """Clear the dead letter queue."""
        count = len(self.dead_letters)
        self.dead_letters.clear()
        logger.info(f"Cleared {count} dead letters")


class ErrorRecoveryManager:
    """Orchestrates error recovery using configured strategies."""
    
    def __init__(self):
        """Initialize error recovery manager."""
        self.strategies: list[ErrorRecoveryStrategy] = []
        self.error_history: list[ErrorContext] = []
        self.max_history_size = 1000
        
        # Initialize default strategies
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """Initialize default recovery strategies."""
        self.add_strategy(RetryStrategy(max_retries=3, initial_delay=1.0))
        self.add_strategy(CircuitBreakerStrategy(failure_threshold=5, reset_timeout=60.0))
        self.add_strategy(DeadLetterStrategy(max_queue_size=1000))
    
    def add_strategy(self, strategy: ErrorRecoveryStrategy):
        """Add a recovery strategy.
        
        Args:
            strategy: Recovery strategy to add.
        """
        self.strategies.append(strategy)
        logger.info(f"Added recovery strategy: {strategy.__class__.__name__}")
    
    async def handle_error(self, error: ErrorContext) -> RecoveryResult:
        """Handle an error using configured strategies.
        
        Args:
            error: Error context.
            
        Returns:
            RecoveryResult from best matching strategy.
        """
        # Track error history
        self._add_to_history(error)
        
        logger.warning(
            f"Handling {error.error_type.value} error in {error.agent_name}: {error.message}"
        )
        
        # Try strategies in order
        for strategy in self.strategies:
            if strategy.can_recover(error):
                result = await strategy.recover(error)
                if result.success:
                    logger.info(f"Recovery succeeded: {result.message}")
                    return result
        
        # No strategy could recover
        logger.error(f"No recovery strategy available for {error.error_type.value}")
        return RecoveryResult(
            success=False,
            message="No applicable recovery strategy found"
        )
    
    def _add_to_history(self, error: ErrorContext):
        """Add error to history for analysis."""
        self.error_history.append(error)
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
    
    def get_error_history(self, agent_name: Optional[str] = None) -> list[ErrorContext]:
        """Get error history, optionally filtered by agent.
        
        Args:
            agent_name: Optional agent name to filter.
            
        Returns:
            List of error contexts.
        """
        if agent_name is None:
            return self.error_history.copy()
        return [e for e in self.error_history if e.agent_name == agent_name]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics.
        
        Returns:
            Dictionary with error statistics.
        """
        if not self.error_history:
            return {"total_errors": 0, "by_type": {}, "by_severity": {}}
        
        by_type = {}
        by_severity = {}
        for error in self.error_history:
            by_type[error.error_type.value] = by_type.get(error.error_type.value, 0) + 1
            by_severity[error.severity.value] = by_severity.get(error.severity.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "by_type": by_type,
            "by_severity": by_severity
        }


# Global error recovery manager instance
_error_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get or create the global error recovery manager.
    
    Returns:
        ErrorRecoveryManager singleton instance.
    """
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager()
    return _error_recovery_manager
