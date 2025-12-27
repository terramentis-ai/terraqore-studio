"""
Security validation utilities for prompt/agent input.

Provides a lightweight prompt-injection defense layer that can be applied
to all agent entry points before delegating to LLMs.
"""

import re
import functools
import logging
from dataclasses import dataclass
from typing import Iterable, Optional, Callable, Any

logger = logging.getLogger(__name__)


class SecurityViolation(Exception):
    """Raised when potentially malicious input is detected."""


@dataclass
class PromptInjectionDefense:
    """Detects common prompt-injection patterns."""

    injection_patterns: Iterable[str] = (
        # Command injection patterns
        r"ignore\s+previous\s+instructions",
        r"system\s+override",
        r"disregard\s+all",
        r"override.*system",
        r"new\s+instructions?",
        r"forget\s+everything",
        r"instructions\s+to\s+follow\s+instead",
        
        # File system operations
        r"delete\s+.*files?",
        r"delete\s+.*\.env",
        r"remove\s+.*files?",
        r"remove\s+.*backups",
        r"unlink\s+",
        r"rm\s+-rf",
        
        # Credential/secret access
        r"access\s+.*credentials?",
        r"access\s+.*secrets?",
        r"access\s+.*password",
        r"show\s+.*password",
        r"database\s+password",
        r"access\s+.*api[_\s]*keys?",
        r"reveal\s+.*api\s*keys?",
        r"reveal\s+.*secret",
        r"secret\s+tokens?",
        
        # Database operations
        r"drop\s+table",
        r"drop\s+database",
        r"truncate\s+",
        r"delete\s+from\s+",
        r"purge\s+.*database",
        
        # System control
        r"shutdown",
        r"restart\s+.*system",
        r"erase\s+.*logs",
        r"kill\s+process",
        r"kill\s+all\s+.*process",
        r"stop\s+.*security\s+monitor",
        r"halt\s+",
        
        # Privilege escalation
        r"sudo\s+",
        r"root\s+access",
        r"admin\b",
        r"escalate.*privilege",
        r"elevate\s+.*privilege",
    )

    def validate_input(self, user_input: str) -> bool:
        """Check a single string for injection attempts."""
        if not user_input:
            return True

        for pattern in self.injection_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                raise SecurityViolation(f"Potential injection detected: {pattern}")
        return True


_defense = PromptInjectionDefense()


def validate_prompt(text: Optional[str]) -> None:
    """Validate a prompt string, raising on violation."""
    if text is None:
        return
    _defense.validate_input(str(text))


def validate_conversation(history: Optional[Iterable[dict]]) -> None:
    """Validate each message in a conversation history."""
    if not history:
        return
    for msg in history:
        content = msg.get("content") if isinstance(msg, dict) else None
        validate_prompt(content)


def validate_context_fields(*fields: Optional[str]) -> None:
    """Validate multiple text fields in a single call."""
    for field in fields:
        validate_prompt(field)


def validate_agent_input(func: Callable) -> Callable:
    """
    Decorator for agent entry points that validates inputs for security violations.
    
    Usage:
        @validate_agent_input
        def execute(self, context: AgentContext) -> AgentResult:
            ...
    
    This decorator:
    - Validates the user_input in AgentContext
    - Validates conversation history if present
    - Validates other context fields
    - Raises SecurityViolation if injection detected
    - Logs all validation attempts
    """
    @functools.wraps(func)
    def wrapper(agent_self, context: Any, *args, **kwargs) -> Any:
        try:
            # Validate user input
            if hasattr(context, 'user_input'):
                validate_prompt(context.user_input)
                logger.debug(f"{agent_self.name}: user_input validated")
            
            # Validate conversation history
            if hasattr(context, 'conversation_history'):
                validate_conversation(context.conversation_history)
                logger.debug(f"{agent_self.name}: conversation_history validated")
            
            # Validate project context fields
            if hasattr(context, 'project_description'):
                validate_prompt(context.project_description)
            if hasattr(context, 'project_name'):
                validate_prompt(context.project_name)
            
            # Call the actual function
            return func(agent_self, context, *args, **kwargs)
            
        except SecurityViolation as e:
            logger.warning(f"{agent_self.name}: Security violation detected - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"{agent_self.name}: Validation error - {str(e)}")
            raise
    
    return wrapper


class SecurityContext:
    """
    Context manager for security validation scope.
    
    Usage:
        with SecurityContext(verbose=True) as ctx:
            validate_prompt(user_input)
            # Violations are collected and can be reviewed
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.violations = []
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.violations and self.verbose:
            logger.info(f"Security context: {len(self.violations)} violation(s) detected")
        return False
    
    def add_violation(self, violation: SecurityViolation):
        """Record a violation within this context."""
        self.violations.append(violation)
        if self.verbose:
            logger.warning(f"Violation: {str(violation)}")